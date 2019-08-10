import logging

import datetime

from pajbot import utils
from pajbot.apiwrappers.dubtrack import DubtrackAPI
from pajbot.managers.redis import RedisManager
from pajbot.models.command import Command
from pajbot.models.command import CommandExample
from pajbot.modules import BaseModule
from pajbot.modules import ModuleSetting

log = logging.getLogger(__name__)


class DubtrackSongInfo:
    """Holds only the info relevant for displaying the song in chat."""

    def __init__(self, song_name, song_link, requester_name):
        self.song_name = song_name
        self.song_link = song_link
        self.requester_name = requester_name


class DubtrackModule(BaseModule):
    AUTHOR = "TalVivian @ github.com/TalVivian"
    ID = __name__.split(".")[-1]
    NAME = "Dubtrack"
    DESCRIPTION = "Gets currently playing song from dubtrack"
    CATEGORY = "Feature"
    SETTINGS = [
        ModuleSetting(
            key="room_name",
            label="Dubtrack room name",
            type="text",
            required=True,
            placeholder="Dubtrack room name (i.e. pajlada)",
            default="pajlada",
            constraints={"min_str_len": 1, "max_str_len": 70},
        ),
        ModuleSetting(
            key="phrase_room_link",
            label="Room link message | Available arguments: {room_name}",
            type="text",
            required=True,
            placeholder="Request your songs at https://dubtrack.fm/join/{room_name}",
            default="Request your songs at https://dubtrack.fm/join/{room_name}",
            constraints={"min_str_len": 1, "max_str_len": 400},
        ),
        ModuleSetting(
            key="phrase_current_song",
            label="Current song message | Available arguments: {song_name}, {song_link}, {requester_name}",
            type="text",
            required=True,
            placeholder="Current song: {song_name}, link: {song_link} requested by {requester_name}",
            default="Current song: {song_name}, link: {song_link} requested by {requester_name}",
            constraints={"min_str_len": 1, "max_str_len": 400},
        ),
        ModuleSetting(
            key="phrase_no_current_song",
            label="Current song message when there's nothing playing",
            type="text",
            required=True,
            placeholder="There's no song playing right now FeelsBadMan",
            default="There's no song playing right now FeelsBadMan",
            constraints={"min_str_len": 1, "max_str_len": 400},
        ),
        ModuleSetting(
            key="phrase_previous_song",
            label="Previous song message | Available arguments: {song_name}, {song_link}, {requester_name}",
            type="text",
            required=True,
            placeholder="Previous song: {song_name}, link: {song_link} requested by {requester_name}",
            default="Previous song: {song_name}, link: {song_link} requested by {requester_name}",
            constraints={"min_str_len": 1, "max_str_len": 400},
        ),
        ModuleSetting(
            key="phrase_no_previous_song",
            label="Previous song message when there's nothing playing",
            type="text",
            required=True,
            placeholder="There's no previous song FeelsBadMan",
            default="There's no previous song FeelsBadMan",
            constraints={"min_str_len": 1, "max_str_len": 400},
        ),
        ModuleSetting(
            key="global_cd",
            label="Global cooldown (seconds)",
            type="number",
            required=True,
            placeholder="",
            default=5,
            constraints={"min_value": 0, "max_value": 120},
        ),
        ModuleSetting(
            key="user_cd",
            label="Per-user cooldown (seconds)",
            type="number",
            required=True,
            placeholder="",
            default=15,
            constraints={"min_value": 0, "max_value": 240},
        ),
        ModuleSetting(key="if_dt_alias", label="Allow !dt as !dubtrack", type="boolean", required=True, default=True),
        ModuleSetting(
            key="if_short_alias",
            label="Allow !dubtrack [s, l, u] as !dubtrack [song, link, update]",
            type="boolean",
            required=True,
            default=True,
        ),
        ModuleSetting(
            key="if_song_alias", label="Alias !song to !dubtrack song", type="boolean", required=True, default=True
        ),
        ModuleSetting(
            key="if_lastsong_alias",
            label="Alias !lastsong to !dubtrack previous",
            type="boolean",
            required=True,
            default=True,
        ),
        ModuleSetting(
            key="if_previoussong_alias",
            label="Alias !previoussong to !dubtrack previous",
            type="boolean",
            required=True,
            default=True,
        ),
    ]

    def __init__(self, bot):
        super().__init__(bot)
        self.api = DubtrackAPI(RedisManager.get())

    def cmd_link(self, bot, **rest):
        bot.say(self.get_phrase("phrase_room_link", room_name=self.settings["room_name"]))

    def cmd_song(self, **rest):
        def on_success(song_info):
            if song_info is not None:
                response = self.get_phrase(
                    "phrase_current_song",
                    song_name=song_info.song_name,
                    song_link=song_info.song_link,
                    requester_name=song_info.requester_name,
                )
            else:
                response = self.get_phrase("phrase_no_current_song")

            self.bot.say(response)

        def on_error(e):
            log.exception("Dubtrack API fetch for current song failed", exc_info=e)
            self.bot.say("There was an error fetching the current dubtrack song monkaS")

        self.api_request_and_callback(self.get_current_song, on_success, on_error)

    def cmd_previous_song(self, **rest):
        def on_success(song_info):
            if song_info is not None:
                response = self.get_phrase(
                    "phrase_previous_song",
                    song_name=song_info.song_name,
                    song_link=song_info.song_link,
                    requester_name=song_info.requester_name,
                )
            else:
                response = self.get_phrase("phrase_no_previous_song")

            self.bot.say(response)

        def on_error(e):
            log.exception("Dubtrack API fetch for previous song failed", exc_info=e)
            self.bot.say("There was an error fetching the previous dubtrack song monkaS")

        self.api_request_and_callback(self.get_current_song, on_success, on_error)

    def api_request_and_callback(self, api_fn, on_success, on_error):
        def action_queue_action():
            try:
                result = api_fn()
                self.bot.execute_now(lambda: on_success(result))
            except Exception as e:
                lol = e
                self.bot.execute_now(lambda: on_error(lol))

        self.bot.action_queue.add(action_queue_action)

    def process_queue_song_to_song_info(self, queue_song):
        """Processes a DubtrackQueueSong instance (from the API) into a DubtrackSongInfo object (for output to chat)"""

        # no current or past song -> no song info
        if queue_song is None:
            return None

        requester_id = queue_song.requester_id
        requester_name = queue_song.requester_name

        # requester_name can be None if queue_song came from api.get_current_song()
        # (Dubtrack does not directly send the requester name in that API response,
        # but requester name is sent on the api.get_past_songs response so it is available
        # directly, not requiring an additional fetch for the username)
        if requester_name is None:
            requester_name = self.api.get_user_name(requester_id)

        song_id = queue_song.song_id
        song_name = queue_song.song_name
        song_link = self.api.get_song_link(song_id)

        return DubtrackSongInfo(song_name=song_name, song_link=song_link, requester_name=requester_name)

    def get_current_song(self):
        room_id = self.api.get_room_id(self.settings["room_name"])
        queue_song = self.api.get_current_song(room_id)

        # consider past songs (this happens if dubtrack is currently switching the playing song)
        if queue_song is None:
            past_songs = self.api.get_past_songs(room_id)
            if len(past_songs) > 0:
                queue_song = past_songs[0]

            if queue_song is not None:
                # it was possible to fetch the last song from the history
                # check using queue_song.length and queue_song.played_at whether
                # this song has ended playing recently
                ended_playing = queue_song.played_at + queue_song.length
                time_since_song_end = utils.now() - ended_playing

                if time_since_song_end > datetime.timedelta(minutes=1):
                    # the song we fetched from the room history ended playing more than 1 minute ago
                    # so it is by no means the "current song" anymore.
                    queue_song = None

        return self.process_queue_song_to_song_info(queue_song)

    def get_previous_song(self):
        room_id = self.api.get_room_id(self.settings["room_name"])

        past_songs = self.api.get_past_songs(room_id)

        if len(past_songs) <= 0:
            queue_song = None
        else:
            queue_song = past_songs[0]

        return self.process_queue_song_to_song_info(queue_song)

    def load_commands(self, **options):
        commands = {
            "link": Command.raw_command(
                self.cmd_link,
                level=100,
                delay_all=self.settings["global_cd"],
                delay_user=self.settings["user_cd"],
                description="Get link to your dubtrack",
                examples=[
                    CommandExample(
                        None,
                        "Ask bot for dubtrack link",
                        chat="user:!dubtrack link\n" "bot:Request your songs at https://dubtrack.fm/join/pajlada",
                    ).parse()
                ],
            ),
            "song": Command.raw_command(
                self.cmd_song,
                level=100,
                delay_all=self.settings["global_cd"],
                delay_user=self.settings["user_cd"],
                description="Get current song",
                examples=[
                    CommandExample(
                        None,
                        "Ask bot for current song (youtube)",
                        chat="user:!dubtrack song\n"
                        "bot:Current song: NOMA - Brain Power, link: https://youtu.be/9R8aSKwTEMg requested by FabPotato69",
                    ).parse(),
                    CommandExample(
                        None,
                        "Ask bot for current song (soundcloud)",
                        chat="user:!dubtrack song\n"
                        "bot:Current song: This is Bondage, link: https://soundcloud.com/razq35/nightlife requested by karylul",
                    ).parse(),
                    CommandExample(
                        None,
                        "Ask bot for current song (nothing playing)",
                        chat="user:!dubtrack song\n" "bot:There's no song playing right now FeelsBadMan",
                    ).parse(),
                ],
            ),
            "previous": Command.raw_command(
                self.cmd_previous_song,
                level=100,
                delay_all=self.settings["global_cd"],
                delay_user=self.settings["user_cd"],
                description="Get previous song",
                examples=[
                    CommandExample(
                        None,
                        "Ask bot for current song (youtube)",
                        chat="user:!dubtrack song\n"
                        "bot:Current song: NOMA - Brain Power, link: https://youtu.be/9R8aSKwTEMg requested by FabPotato69",
                    ).parse(),
                    CommandExample(
                        None,
                        "Ask bot for current song (soundcloud)",
                        chat="user:!dubtrack song\n"
                        "bot:Current song: This is Bondage, link: https://soundcloud.com/razq35/nightlife requested by karylul",
                    ).parse(),
                    CommandExample(
                        None,
                        "Ask bot for current song (nothing playing)",
                        chat="user:!dubtrack song\n" "bot:There's no song playing right now FeelsBadMan",
                    ).parse(),
                ],
            ),
        }

        # alias :p
        commands["lastsong"] = commands["previous"]

        if self.settings["if_short_alias"]:
            commands["l"] = commands["link"]
            commands["s"] = commands["song"]

        self.commands["dubtrack"] = Command.multiaction_command(
            level=100,
            default="link",  # If the user does not input any argument
            fallback="link",  # If the user inputs an invalid argument
            command="dubtrack",
            commands=commands,
        )

        if self.settings["if_dt_alias"]:
            self.commands["dt"] = self.commands["dubtrack"]

        if self.settings["if_song_alias"]:
            self.commands["song"] = commands["song"]

        if self.settings["if_previoussong_alias"]:
            self.commands["previoussong"] = commands["previous"]

        if self.settings["if_lastsong_alias"]:
            self.commands["lastsong"] = commands["previous"]
