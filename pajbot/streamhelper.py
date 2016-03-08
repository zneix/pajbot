import collections


class StreamHelper:
    """ Staticly available class with a bunch of useful variables.
    streamer: The name of the streamer in full lowercase
    stream_id: The ID of the current stream. False if the stream is not live
    """

    streamer = 'Unknown'
    stream_manager = None
    social_keys_unsorted = {
            'twitter': {
                'format': 'https://twitter.com/{}',
                'title': 'Twitter',
                },
            'github': {
                'format': 'https://github.com/{}',
                'title': 'Github',
                },
            'youtube': {
                'format': '{}',
                'title': 'YouTube',
                },
            'instagram': {
                'format': 'https://www.instagram.com/{}/',
                'title': 'Instagram',
                },
            'reddit': {
                'format': 'https://www.reddit.com/r/{}/',
                'title': 'Reddit',
                },
            'steam': {
                'format': '{}',
                'title': 'Steam',
                },
            'facebook': {
                'format': '{}',
                'title': 'Facebook',
                },
            }
    social_keys = collections.OrderedDict(sorted(social_keys_unsorted.items(), key=lambda t: t[0]))
    valid_social_keys = set(social_keys.keys())

    def init_bot(bot, stream_manager):
        StreamHelper.init_streamer(bot.streamer)
        StreamHelper.stream_manager = stream_manager

    def init_web(streamer):
        StreamHelper.init_streamer(streamer)

    def init_streamer(streamer):
        StreamHelper.streamer = streamer

    def get_streamer():
        return StreamHelper.streamer

    def get_current_stream_id():
        """ Gets the stream ID of the current stream.
        Returns False if the stream manager has not been initialized.
        Returns False if there is no stream online.
        Returns the current streams ID (integer) otherwise.
        """

        if StreamHelper.stream_manager is None:
            # Stream manager not initialized, web interface?
            return None

        if StreamHelper.stream_manager.current_stream is None:
            # Stream is offline
            return False

        return StreamHelper.stream_manager.current_stream.id

    def get_last_stream_id():
        """ Gets the stream ID of the last stream.
        Returns False if the stream manager has not been initialized.
        Returns False if there is no stream online.
        Returns the current streams ID (integer) otherwise.
        """

        if StreamHelper.stream_manager is None:
            # Stream manager not initialized, web interface?
            return None

        if StreamHelper.stream_manager.last_stream is None:
            # Stream is offline
            return False

        return StreamHelper.stream_manager.last_stream.id
