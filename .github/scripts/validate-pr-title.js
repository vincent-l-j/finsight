// validate-pr-title.js
const conventionalCommitRegex = /^(feat|fix|perf|revert|docs|style|chore|refactor|test|build|ci)(\(.+\))?: .{1,100}/;

const prTitle = process.argv[2];

if (!conventionalCommitRegex.test(prTitle)) {
  console.error("error: Pull request title does not follow conventional commit format.");
  process.exit(1);
}
