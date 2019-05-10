/**
 * See README (Настройка окружения) doc for details.
 * This gulp script requires Docker installed on your host machine
 */

const gulp = require("gulp");
const lambda = require("gulp-lambda-deploy");
const zip = require("gulp-zip");
const del = require("del");
const util = require('util');
const exec = util.promisify(require('child_process').exec);

const path = {
    lambda_sources: ["./lambda_src/**/*.*"],
    dist_folder: "./dist/",
    zip_dist_file: "dist.zip",
    dependencies_src: "./venv/lib/python3.6/site-packages/**/*.*",
    dist_sources: "./dist/**/*.*"
};


async function dockerBuild() {
    // run a command in a shell
    // requires Docker installed
    const cmd = 'docker run -it -v $PWD:/var/task lambci/lambda:build-python3.6 bash';
    const {stdout, stderr} = await exec(cmd);
    if (stderr) throw new Error(stderr)
}

async function installRequirements() {
    // run a command in a shell
    const [activateCmd, installRequirements] = ["source ./venv/bin/activate", "pip install -r requirements.txt"];
    const {stdoutActivateCmd, stderrActivateCmd} = await exec(activateCmd);
    if (stderrActivateCmd) throw new Error(stderr);
    const {stdoutInstallCmd, stderrInstallCmd} = await exec(installRequirements);
    if (stderrInstallCmd) throw new Error(stderr)
}

gulp.task("clean", cb =>
    del('./dist',
        del('./archive.zip', cb)
    )
);

gulp.task("sources", _ =>
    gulp.src(path.lambda_sources)
        .pipe(gulp.dest(path.dist_folder))
);

gulp.task("dependenciesBuild", async (cb) => {
    await dockerBuild();
    await installRequirements();
    return cb()
});

gulp.task("dependencies", _ =>
    gulp.src(path.dependencies_src)
        .pipe(gulp.dest(path.dist_folder))
);

gulp.task("zip", _ =>
    gulp.src(path.dist_sources)
        .pipe(zip(path.zip_dist_file))
        .pipe(gulp.dest('./'))
);

const params = {
    name: "<Your function name>",
    role: "arn:aws:iam::<Lamda ID>:role/service-role/defaultRole",
    runtime: "python3.6",
    handler: "main.handler"
};

const options = {
    profile: "default",
    region: "eu-west-1"
};

gulp.task("upload", cb =>
    gulp.src(path.zip_dist_file)
        .pipe(lambda(params, options))
        .on('end', cb)
);

gulp.task('default',
    gulp.series(
        ["clean"],
        ["dependenciesBuild"],
        ["dependencies", "sources"],
        ['zip'],
        ['upload'],
        done => done()
    ));