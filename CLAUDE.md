# Testing changes

After making any code, config, or prompt changes, always re-run `./venv/bin/python main.py` to send a fresh test email. The local venv has Mailgun and Anthropic keys configured, and the run is the only way to verify how the email actually renders end-to-end. Don't wait to be asked.
