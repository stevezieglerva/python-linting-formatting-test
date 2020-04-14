cp -R input/ output/

pylint --exit-zero -ry --rcfile=.pylintrc_tabs input/ | grep rated > pylint_scores.txt


black output/
pylint --exit-zero -ry --rcfile=.pylintrc_spaces output/ | grep rated >> pylint_scores.txt


