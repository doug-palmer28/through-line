"""The graders' setup: every repo is cloned into one folder, and the shared .env sits one level above the repo.
The app must find the key there, even if the repo has its own .env (for example an untouched copy of .env.example)."""

import os

import config

KEY = "THROUGH_LINE_ENV_TEST_KEY"  # a made-up name, so no real key is ever involved


def _setup(tmp_path, monkeypatch, repo_env: str | None):
    repo = tmp_path / "submissions" / "through-line"
    repo.mkdir(parents=True)
    (tmp_path / "submissions" / ".env").write_text(f"{KEY}=from-the-folder-above\n", encoding="utf-8")
    if repo_env is not None:
        (repo / ".env").write_text(repo_env, encoding="utf-8")
    monkeypatch.setattr(config, "PROJECT_DIR", repo)
    monkeypatch.delenv(KEY, raising=False)


def test_key_is_found_one_folder_above_the_repo(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, repo_env=None)
    config._load_env()
    assert os.environ[KEY] == "from-the-folder-above"


def test_a_blank_copy_of_env_example_does_not_hide_it(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, repo_env=f"{KEY}=\n")
    config._load_env()
    assert os.environ[KEY] == "from-the-folder-above"


def test_the_repos_own_env_comes_first(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, repo_env=f"{KEY}=from-the-repo\n")
    config._load_env()
    assert os.environ[KEY] == "from-the-repo"


def test_a_value_already_in_the_environment_wins(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, repo_env=None)
    monkeypatch.setenv(KEY, "")  # how the offline tests keep a key out on purpose
    config._load_env()
    assert os.environ[KEY] == ""
