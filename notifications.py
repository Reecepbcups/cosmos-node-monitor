from discord_webhook import DiscordEmbed, DiscordWebhook


# https://github.com/Reecepbcups/hetzner-storage-backup/blob/main/src/notifications.py
def discord_notification(
    url="",
    title="",
    description="",
    color="ffffff",
    values={},
    imageLink="",
    footerText="",
):
    webhook = DiscordWebhook(url=url)

    embed = DiscordEmbed(title=title, description=description, color=color)
    # # set thumbnail
    embed.set_thumbnail(url=imageLink)

    embed.set_footer(text=footerText)
    embed.set_timestamp()

    for k, v in values.items():
        embed.add_embed_field(name=k, value=v[0], inline=v[1])

    webhook.add_embed(embed)
    response = webhook.execute()
