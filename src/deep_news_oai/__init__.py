"""Deep News OAI - OpenAI ChatGPT App for Korean News Analysis."""

__version__ = "0.1.0"


def main():
    """CLI entrypoint."""
    from deep_news_oai.server import run_server
    run_server()
