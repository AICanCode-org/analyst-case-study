# R track (tidyverse + base R stats + R Markdown). Same targets in every track:
# install, lint, test, coverage, run (+ report).
R ?= Rscript
DATA ?= ../../data/raw/2026-08
OUT ?= out

.PHONY: install lint test coverage run report clean
install:         ## the packages in DESCRIPTION (CI uses r-lib/actions/setup-r-dependencies instead)
	$(R) -e 'install.packages(c("pak"), repos = "https://cloud.r-project.org"); pak::local_install_deps(dependencies = TRUE)'

lint:
	$(R) -e 'l <- lintr::lint_package("."); print(l); if (length(l) > 0) quit(status = 1)'

test:            ## unit tests (fast, tiny fixtures)
	$(R) -e 'testthat::test_local(".", filter = "^unit-", reporter = "summary", stop_on_failure = TRUE)'

coverage:        ## unit + data tests on the real export, 85 % line coverage gate
	$(R) tools/coverage.R 85

run:             ## answers.json for one export
	$(R) run.R run --data $(DATA) --out $(OUT)

report:          ## knit report/analysis.Rmd to out/analysis.html (fails on any error)
	$(R) -e 'd <- normalizePath("$(DATA)"); o <- normalizePath("$(OUT)", mustWork = FALSE); rmarkdown::render("report/analysis.Rmd", output_dir = o, params = list(data = d), quiet = TRUE)'

clean:
	rm -rf $(OUT) coverage.xml report/*_files report/*.html
