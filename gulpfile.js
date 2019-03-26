const gulp = require("gulp");
const lambda = require("gulp-lambda-deploy");
const zip = require("gulp-zip");
const del = require("del");
const AWS = require("aws-sdk");
const gutil = require("gulp-util");

const path = {
    lambda_sources: ["./lambda_src/**/*.*"],
    dist_folder: "./dist/",
    zip_dist_file: "dist.zip",
    pymorphy_lib: "./venv/lib/python3.7/site-packages/pymorphy2/**/*.*",
    pymorphy_dicts_lib: "./venv/lib/python3.7/site-packages/pymorphy2_dicts/**/*.*",
    dawg_python_lib: "./venv/lib/python3.7/site-packages/dawg_python/**/*.*",
    nltk_lib: "./venv/lib/python3.7/site-packages/nltk/**/*.*",
    dependencies_src: "./venv/lib/python3.6/site-packages/**/*.*",
    dist_sources: "./dist/**/*.*"
};

gulp.task("clean", cb =>
    del('./dist',
        del('./archive.zip', cb)
    )
);

gulp.task("pymorphy2", _ =>
    gulp.src(path.pymorphy_lib)
        .pipe(gulp.dest(path.dist_folder + "pymorphy2"))
);

gulp.task("pymorphy2_dicts", _ =>
    gulp.src(path.pymorphy_dicts_lib)
        .pipe(gulp.dest(path.dist_folder + "pymorphy2_dicts"))
);

gulp.task("dawg_python", _ =>
    gulp.src(path.dawg_python_lib)
        .pipe(gulp.dest(path.dist_folder + "dawg_python"))
);

gulp.task("numpy", _ =>
    gulp.src(path.numpy_lib)
        .pipe(gulp.dest(path.dist_folder + "numpy"))
);

gulp.task("nltk", _ =>
    gulp.src(path.nltk_lib)
        .pipe(gulp.dest(path.dist_folder + "nltk"))
);

gulp.task("sources", _ =>
    gulp.src(path.lambda_sources)
        .pipe(gulp.dest(path.dist_folder))
);

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
    name: "Highlights-random",
    role: "arn:aws:iam::632759214929:role/service-role/defaultRole",
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
        ["dependencies", "sources"],
        ['zip'],
        ['upload'],
        done => done()
    ));