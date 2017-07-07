import discord
from eventbot import ErrorMessages, get_event, get_event_channel, set_event_channel

# command messages
creator_id = '175753699224715264' # my discord user id
github_link = 'https://github.com/desolt/EventBot'
info_embed = discord.Embed(title='EventBot', 
                           type='rich', 
                           description='Helps discord admins manage events!\n\n' \
                                       'Created by <@{}>'.format(creator_id),
                           url=github_link)
info_embed.set_thumbnail(url='http://www.thefamouspeople.com/profiles/images/huey-long-2.jpg')

commands_message = '```css\n' \
                   'eb!info - shows this menu.\n' \
                   'eb!eventchannel <channel>\n' \
                   'eb!event <name> <mm/dd/yy> <hh:mm UTC> - schedules an event\n' \
                   'eb!repeat <id> - toggles whether an event should repeat each week.\n' \
                   'eb!events [page #] - shows the current scheduled events\n' \
                   'eb!cancel <id> - cancels an event\n' \
                   'eb!subscribe <id> - subscribes to an event\n' \
                   'eb!unsubscribe <id> - unsubscribes from an event\n' \
                   'eb!subscriptions [page #] - lists subscribed events (DM only)\n' \
                   '```'

# Helper functions
async def get_pos_num_at(args, index, bot):
    if len(args) < index:
        await bot.send_message(message.channel, ErrorMessages.INVALID_ARG)
        raise ValueError('There must be two arguments to access the page number.')

    try:
        x = int(args[index])
        if x < 0: raise ValueError('The number must be postiive!')
    except ValueError as e: 
        await bot.send_message(message.channel, ErrorMessages.BAD_PAGE_NUM)
        raise e
    return x
    
async def print_events(target, events, page, bot):
    desc = ''
    for event in events:
        desc += '**ID:** {}\n'.format(event['id'])
        desc += '**Name**: {}\n'.format(event['name'])
        desc += '**Server**: {}\n'.format(bot.get_server(event['serverid']).name)
        desc += '**When:** {}\n\n'.format(event['startsat'].strftime('%m/%d/%y %I:%M%p UTC'))
    embed = discord.Embed(title = 'Page #{}:'.format(page), color = 0xdafc1b, description = desc)
           
    await bot.send_message(target, embed = embed)

async def get_event(args, id_at, bot):
    event_id = await get_pos_num_at(args, id_at, bot)
    from eventbot import event_table
    event = event_table.find_one(id = event_id)
    if event is None:
        await bot.send_message(message.channel, ErrorMessages.BAD_EVENT)
        raise ValueError('No event for event id {} at {}'.format(event_id, id_at))
    else:
        return event


# Commands
async def info(bot, args, message):
    if len(args) == 1:
        await bot.send_message(message.channel, embed = info_embed)
        await bot.send_message(message.author, 'Commands:\n{}'.format(commands_message))
        if not message.channel.is_private: # No point in saying commands have been DMed in the DMs.
            await bot.send_message(message.channel, 'The commands have been DMed to you!')
    else:
        await bot.send_message(message.channel, ErrorMessages.INVALID_ARG)

async def eventchannel(bot, args, message):
    if len(args) == 1:
        channel = await get_event_channel(message.server, bot)
        await bot.send_message(message.channel, 'The event channel is <#{}>.'.format(channel.id))
    elif len(args) == 2:
        try:
            new_channel = message.channel_mentions[0]
            await set_event_channel(message.server, new_channel)
            await bot.send_message(message.channel, '<#{}> is now the event channel!'.format(new_channel.id))
        except KeyError:
            await bot.send_message(message.channel, 'No channel mentioned! ex: eb!eventchannel #general')
    else:
        await bot.send_message(message.channel, ErrorMessages.INVALID_ARG)

async def subscribe(bot, args, message):
    if len(args != 2):
        bot.send_message(message.channel, ErrorMessages.INVALID_ARG)
        return

    try: event = get_event(args, args[1], bot)
    except: return

    from eventbot import subscription_table
    subscription_exists = subscription_table.find_one(userid = message.author.id, 
                                                      eventid = event['id'])
    if subscription_exists is None:
        subscription_table.insert(dict(userid = message.author.id, 
                                       eventid = event['id']))
        await bot.send_message(message.channel, 'You are now subscribed to event #{}!'.format(event['id']))
    else:
        await bot.send_message(message.channel, 'You are already subscribed to that event!')

async def event(bot, args, message): 
    if message.channel.is_private: return
    # Only admins can make events. TODO: Allow custom roles to make events w/ server settings
    if not message.channel.permissions_for(message.author).administrator:
        await bot.send_message(message.channel, ErrorMessages.PERMISSION)
        return

    if len(args) != 4:
        await bot.send_message(message.channel, ErrorMessages.INVALID_ARG)
        return

    dtstr = '{} {}'.format(args[2], args[3])
    try:
       dtobj = datetime.strptime(dtstr, '%m/%d/%y %H:%M')
       if datetime.utcnow() > dtobj:
            await bot.send_message(message.channel, 'An event should take place in the future! (Remember to use UTC)')
            return
    except ValueError:
        await bot.send_message(message.channel, 'Invalid datetime format!')
        return
            
    from eventbot import event_table
    id = event_table.insert(dict(name = args[1], serverid = message.server.id, startsat = dtobj, repeat = False))

    embed = discord.Embed(title = 'Created a new event!', 
                          description = args[1], 
                          color = 0x5cc0f2, # Color is a nice sky blue.
                          type = 'rich')
    embed.add_field(name = 'ID', value = str(id))
    embed.add_field(name = 'When', value = dtobj.strftime('%m/%d/%y %I:%M%p'))
    await bot.send_message(message.channel, embed = embed)


commands = {
    'info': info,
    'help': info,
    'eventchannel': eventchannel,
    'subscribe': subscribe,
    'event': event,
}
