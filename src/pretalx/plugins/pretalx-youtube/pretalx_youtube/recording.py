from pretalx.agenda.recording import BaseRecordingProvider


class YouTubeProvider(BaseRecordingProvider):
    def get_recording(self, submission):
        youtube = getattr(submission, "youtube_link", None)
        if youtube:
            return {
                "iframe": youtube.iframe,
                # NOVA: THIS is a hacky change so that etherpad iframes work. Not the optimal solution, but less complex
                "csp_header": "*" # "https://www.youtube-nocookie.com/",
            }
