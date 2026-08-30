module.exports = {
  apps: [
    {
      name: "tgdrive-bot",
      script: "./venv/bin/python",
      args: "bot.py",
      interpreter: "none",
      cwd: __dirname,
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 5000
    }
  ]
};
