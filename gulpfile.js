const gulp = require("gulp");
const lambda = require("gulp-lambda-deploy");
const zip = require("gulp-zip");
const del = require("del");
const AWS = require("aws-sdk");
const gutil = require("gulp-util");

const path = {
    lambda_sources: ["./lambda_src/**/*.*"],
    lambda_sources_embeddings: ["./lambda_src_embeddings/**/*.*"],
    dist_folder: "./dist/",
    zip_dist_file: "dist.zip",
    pymorphy_lib: "./venv/lib/python3.7/site-packages/pymorphy2/**/*.*",
    pymorphy_dicts_lib: "./venv/lib/python3.7/site-packages/pymorphy2_dicts/**/*.*",
    future_lib: "./venv/lib/python3.7/site-packages/future/**/*.*",
    requests_lib: "./venv/lib/python3.7/site-packages/requests/**/*.*",
    chardet_lib : "./venv/lib/python3.7/site-packages/chardet/**/*.*",
    certifi_lib : "./venv/lib/python3.7/site-packages/certifi/**/*.*",
    idna_lib : "./venv/lib/python3.7/site-packages/idna/**/*.*",
    pymystem3_lib: "./venv/lib/python3.7/site-packages/pymystem3/**/*.*",
    dawg_python_lib: "./venv/lib/python3.7/site-packages/dawg_python/**/*.*",
    nltk_lib: "./venv/lib/python3.7/site-packages/nltk/**/*.*",
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

gulp.task("future", _ =>
    gulp.src(path.future_lib)
        .pipe(gulp.dest(path.dist_folder + "future"))
);

gulp.task("pymystem3", _ =>
    gulp.src(path.pymystem3_lib)
        .pipe(gulp.dest(path.dist_folder + "pymystem3"))
);

gulp.task("sources", _ =>
    gulp.src(path.lambda_sources)
        .pipe(gulp.dest(path.dist_folder))
);

gulp.task("requests", _ =>
    gulp.src(path.requests_lib)
        .pipe(gulp.dest(path.dist_folder + "requests"))
);

gulp.task("chardet", _ =>
    gulp.src(path.chardet_lib)
        .pipe(gulp.dest(path.dist_folder + "chardet"))
);

gulp.task("certifi", _ =>
    gulp.src(path.certifi_lib)
        .pipe(gulp.dest(path.dist_folder + "certifi"))
);

gulp.task("idna", _ =>
    gulp.src(path.idna_lib)
        .pipe(gulp.dest(path.dist_folder + "idna"))
);

gulp.task("sources_embeddings", _ =>
    gulp.src(path.lambda_sources_embeddings)
        .pipe(gulp.dest(path.dist_folder))
);

gulp.task("zip", _ =>
    gulp.src(path.dist_sources)
        .pipe(zip(path.zip_dist_file))
        .pipe(gulp.dest('./'))
);

const params = {
    name: "Highlights",
    role: "arn:aws:iam::701551728765:role/service-role/defaultRole",
    runtime: "python3.7",
    handler: "main.handler"
};

const paramsEmbeddings = {
    name: "highlights_word_embeddings",
    role: "arn:aws:iam::701551728765:role/service-role/defaultRole",
    runtime: "python3.7",
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

gulp.task("upload_embeddings", cb =>
    gulp.src(path.zip_dist_file)
        .pipe(lambda(paramsEmbeddings, options))
        .on('end', cb)
);

gulp.task('default',
    gulp.series(
        ["clean"],
        ["pymorphy2", "dawg_python", "nltk", "pymorphy2_dicts", "sources"],
        ['zip'],
        ['upload'],
        done => done()
    ));

gulp.task('embeddings',
    gulp.series(
        ["clean"],
        ["pymorphy2", "dawg_python", "nltk", "pymorphy2_dicts", "sources_embeddings", "future",
            "pymystem3", "requests", "chardet", "certifi", "idna"],
        ['zip'],
        ['upload_embeddings'],
        done => done()
    ));