# Read about [DIP](https://roman-corgi.github.io/ctc-dip/)

## Mechanics of Contributing

1. Optional: create an issue and assign it a milestone
1. Chose the issue to work, like issue #23
1. In you local ctc-dip repository
    1. `git switch main`
    1. `git pull origin`
    1. `git checkout -b i-<issue number>` continuing the #23 example `git checkout -b i-23`
    1. `git push --set-upstream origin i-<issue number>` continuisng the #23 example `git push --set-upstream origin i-23`
1. Put only code changes required for the issue on the branch; meaning, make a new branch for every issue.
1. Push as often as desired using github.com as the backup of your work in progress.
1. Create a PR when the disucssion changes from the issue to the solution. In other words, discussing the issue for clarification or options should be done on the issue. Discussing implementation details like a for or while loop should be done on a PR.
1. When the PR clears all of its checks and has been reviewed, squash and merge it. Take this time to rewrite the commit message. Remove all unimportant messages about making fixes for linters or indentation. Make the message more comphrensive and a summary.
