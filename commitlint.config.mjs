export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "body-max-line-length": [0],
    "footer-max-line-length": [0],
    "type-enum": [
      2,
      "always",
      ["build", "chore", "ci", "docs", "feat", "fix", "perf", "refactor", "revert", "style", "test"],
    ],
  },
  // Dependabot copies the capitalization of its previous commits on main, so only its `chore(deps…): Bump` subjects are exempt; every other commit must keep a lowercase subject.
  ignores: [(message) => /^chore\(deps(-dev)?\): Bump /.test(message)],
};
