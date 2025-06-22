"""
This modules serves to deploy the python app on an uberspace account.
Originally based on this tutorial: <https://lab.uberspace.de/guide_django.html>.
"""

import time
import os
import os
from os.path import join as pjoin
from pathlib import Path

# these packages are not in requirements.txt but in deployment_requirements.txt
# noinspection PyUnresolvedReferences
# noinspection PyUnresolvedReferences
from ipydex import IPS, activate_ips_on_exception

REQUIREMENTS_INSTALLED = None

try:
    from packaging import version
    min_du_version = version.parse("0.9.0")
    # this is not listed in the requirements because it is not needed on the deployment server
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import deploymentutils as du

    vsn = version.parse(du.__version__)
    if vsn < min_du_version:
        print(f"You need to install `deploymentutils` in version {min_du_version} or later. Quit.")
        exit()

except ImportError as err:
    print("You need to install the package `deploymentutils` to run the deployment")
else:
    REQUIREMENTS_INSTALLED = True

class DeploymentError(ValueError):
    pass


class DeploymentManager:
    def __init__(self, args):


        # call this before running the script:
        # eval $(ssh-agent); ssh-add -t 10m

        # hopefully this is not needed for the command line usage
        # workdir = os.path.abspath(os.getcwd())
        # msg = (
        #     "This deployment script is expected to be run from the BASEDIR of the project repo, i.e. "
        #     "from the same directory where `LICENSE` lives and the subdir deployment is located. "
        #     "This seems not to be the case.\n"
        #     f"Your current workdir is {workdir}"
        # )

        # if not os.path.isdir(pjoin(workdir, "deployment")):
        #     raise FileNotFoundError(msg)

        # simplify debugging
        activate_ips_on_exception()

        configfile = getattr(args, "configfile")
        assert configfile is not None

        # load exact configfile
        self.config = du.get_nearest_config(os.path.abspath(configfile))

        self.remote = self.config("dep::remote")
        self.user = self.config("dep::user")

        # this is the root dir of the project repo (where setup.py lies)
        self.repo_src_path = Path(du.get_dir_of_this_file()).parents[1].as_posix()
        assert os.path.isfile(os.path.join(self.repo_src_path, "LICENSE"))

        self.repo_parent_src_path = os.path.dirname(self.repo_src_path)

        # directory for deployment files (e.g. database files)
        self.app_name = self.config("dep::app_name")
        self.project_name = self.config("dep::PROJECT_NAME")

        # this is needed to distinguish different django/flask instances on the same uberspace account
        self.port = self.config("dep::port")

        self.asset_dir = pjoin(du.get_dir_of_this_file(), "files")  # contains the templates
        self.temp_workdir = pjoin(du.get_dir_of_this_file(), "tmp_workdir")  # this will be deleted/overwritten

        # -------------------------- End Config section -----------------------

        # it should not be necessary to change the data below, but it might be interesting what happens.
        # (After all, this code runs on your computer/server under your responsibility).



        # name of the directory for the virtual environment:
        self.venv = self.config("dep::venv")
        self.venv_path = f"/home/{self.user}/{self.venv}"

        # because uberspace offers many python versions:
        self.pipc = self.config("dep::pip_command")
        self.python_version = self.config("dep::python_version")

        self.uwsg_service_name = f'uwsgi-{self.config("dep::PROJECT_NAME")}'

        self.args = args

        self.final_msg = f"Deployment script {du.bgreen('done')}."
        self.target_deployment_root_path = self.config("dep::deployment_path")
        self.target_deployment_workdir_path = f"{self.target_deployment_root_path}"

        if not self.args.target == "remote":
            raise NotImplementedError("local deployment is currently not supported")

        # print a warning for data destruction
        du.warn_user(
            self.app_name,
            self.args.target,
            self.args.unsafe,
            deployment_path=self.target_deployment_root_path,
            user=self.user,
            host=self.remote,
        )

        # ensure clean workdir
        os.system(f"rm -rf {self.temp_workdir}")
        os.makedirs(self.temp_workdir)

        self.c = du.StateConnection(self.remote, user=self.user, target=self.args.target)

        return None  # end of __init__

    @staticmethod
    def add_deployment_args(parser: None):
        """
        Amend the default arguments implemented in deployment utils package

        :param parser:      subparser (see cli.py)
        """
        parser.add_argument("configfile", help="specify path to configfile")

        for action in du.argparser._actions:
            parser._add_action(action)

        parser.add_argument("-p", "--purge", help="purge target directory before deploying", action="store_true")
        parser.add_argument("--debug", help="start debug interactive mode (IPS), then exit", action="store_true")

        # remove non-optional argument:
        for a in parser._actions:
            if a.choices and set(a.choices) == set(("local", "remote")):
                a.default = "remote"
                a.required = False

    def create_and_setup_venv(self):

        c = self.c

        # TODO: check if venv exists

        c.run(f"{self.pipc} install --user virtualenv")

        print("create and activate a virtual environment inside $HOME")
        c.chdir("~")

        c.run(f"rm -rf {self.venv}")
        c.run(f"{self.python_version} -m virtualenv -p {self.python_version} {self.venv}")

        c.activate_venv(f"~/{self.venv}/bin/activate")

        c.run(f"pip install --upgrade pip")
        c.run(f"pip install --upgrade setuptools")

        print("\n", "install uwsgi", "\n")
        c.run(f"pip install uwsgi")

        # ensure that the same version of deploymentutils like on the controller-pc is also in the server
        c.deploy_this_package()

    def render_and_upload_config_files(self):

        c = self.c
        c.activate_venv(f"~/{self.venv}/bin/activate")

        # generate the general uwsgi ini-file
        tmpl_dir = os.path.join("uberspace", "etc", "services.d")
        tmpl_name = "template_PROJECT_NAME_uwsgi.ini"
        target_name = "PROJECT_NAME_uwsgi.ini".replace("PROJECT_NAME", self.project_name)
        du.render_template(
            tmpl_path=pjoin(self.asset_dir, tmpl_dir, tmpl_name),
            target_path=pjoin(self.temp_workdir, tmpl_dir, target_name),
            context=dict(
                venv_abs_bin_path=f"{self.venv_path}/bin/",
                project_name=self.project_name,
                deployment_root_path=self.target_deployment_root_path,
            ),
        )

        # generate config file for uwsgi-app
        tmpl_dir = pjoin("uberspace", "uwsgi", "apps-enabled")
        tmpl_name = "template_PROJECT_NAME.ini"
        target_name = "PROJECT_NAME.ini".replace("PROJECT_NAME", self.project_name)
        du.render_template(
            tmpl_path=pjoin(self.asset_dir, tmpl_dir, tmpl_name),
            target_path=pjoin(self.temp_workdir, tmpl_dir, target_name),
            context=dict(
                venv_dir=f"{self.venv_path}",
                deployment_root_path=self.target_deployment_root_path,
                port=self.port,
                user=self.user,
                url_path=self.config("dep::url_path"),
                app_name=self.config("dep::app_name"),
            ),
        )

        #
        # ## upload config files to remote $HOME ##
        #
        srcpath1 = os.path.join(self.temp_workdir, "uberspace")
        filters = "--exclude='**/README.md' --exclude='**/template_*'"  # not necessary but harmless
        c.rsync_upload(srcpath1 + "/", "~", filters=filters, target_spec="remote")

    def update_supervisorctl(self):
        c = self.c

        c.activate_venv(f"~/{self.venv}/bin/activate")

        c.run("supervisorctl reread", target_spec="remote")
        c.run("supervisorctl update", target_spec="remote")
        print("waiting 10s for uwsgi to start")
        time.sleep(10)

        res1 = c.run("supervisorctl status", target_spec="remote")

        assert "uwsgi" in res1.stdout
        assert "RUNNING" in res1.stdout

    def set_web_backend(self):
        c = self.c
        c.activate_venv(f"~/{self.venv}/bin/activate")

        c.run(
            f'uberspace web backend set {self.config("dep::url_path")} --http --port {self.port}'
        )

    def upload_app_files(self):
        c = self.c

        print("\n", "ensure that deployment path exists", "\n")
        c.run(f"mkdir -p {self.target_deployment_root_path}")

        print("\n", "upload current project-root including workdir", "\n")

        filters = f" --exclude='.idea/'  --exclude='.vscode/' --exclude='*aider*' --exclude='.git/*'"

        # NOTE: we upload only the repo, not the surrounding dir (like in other projects)
        c.rsync_upload(
            self.repo_src_path + "/", self.target_deployment_root_path, filters=filters, target_spec="both"
        )

        # c.rsync_upload(
        #     self.repo_parent_src_path + "/", self.target_deployment_root_path, filters=filters, target_spec="both"
        # )


    def purge_deployment_dir(self):
        c = self.c
        answer = input(f" -> {du.yellow('purging')} <{self.args.target}>/{self.target_deployment_root_path} (y/N)")
        if answer != "y":
            print(du.bred("Aborted."))
            exit()
        c.run(f"rm -r {self.target_deployment_root_path}", target_spec="both")

    def install_app(self):
        c = self.c
        c.activate_venv(f"~/{self.venv}/bin/activate")

        c.chdir(self.target_deployment_root_path)
        c.run("pip install -r requirements.txt", target_spec="both")
        c.run("pip install -e .", target_spec="both")
        pycmd = "import time; print(time.strftime(r'%Y-%m-%d %H:%M:%S'))"
        c.run(f"""python3 -c "{pycmd}" > deployment_date.txt""", target_spec="remote")



def main(dm: DeploymentManager = None, **kwargs):

    if dm is None:
        dm = DeploymentManager(**kwargs)

    if dm.args.purge:
        dm.purge_deployment_dir()

    if dm.args.debug:
        # dm.set_web_backend()
        dm.upload_app_files()
        exit()

        ## create_and_setup_venv()

        # dm.upload_flabbs_repo()
        # dm.activate_workers()
        # dm.render_and_upload_config_files()

        # dm.update_supervisorctl()



        # dm.c.activate_venv(f"{dm.venv_path}/bin/activate")
        # dm.c.deploy_this_package()
        # dm.install_app()
        # render_and_upload_config_files()
        # IPS()
        exit()

        # c.deploy_local_package("/home/ck/projekte/rst_python/ipydex/repo")
        # render_and_upload_config_files()
        # c.run(f"supervisorctl restart {uwsg_service_name}")

        exit()

    if dm.args.initial:

        dm.create_and_setup_venv()
        dm.upload_app_files()
        dm.render_and_upload_config_files()
        dm.update_supervisorctl()
        dm.set_web_backend()

    if dm.args.purge:
        dm.purge_deployment_dir()

    dm.render_and_upload_config_files()

    dm.upload_app_files()
    dm.install_app()
    print("\n", "restart uwsgi service", "\n")
    dm.c.run(f"supervisorctl restart {dm.uwsg_service_name}")


    print(dm.final_msg)
