A BASED discord bot allowing players to create custom card decks, to play a game inspired by Cards Against Humanity.

Cards are pulled from a linked google spreadsheet. If your spreadsheet is not publicly readable, please ensure it is readable by your google API account. The API account for the official deploy of super deck breaker is: `list-sheets@superdeckbreaker.iam.gserviceaccount.com`

## Deployment


The `deploy` folder contains files and configurations for a minimum `docker-compose` deployment.
To deploy:

```bash
$ cd deploy
$ echo "SDB_BOT_TOKEN=discordtokenhere" > bot_token.sh
$ # Create a config.toml file for the bot in the deploy directory
$ docker-compose up -d
```
