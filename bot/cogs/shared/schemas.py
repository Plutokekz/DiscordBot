from typing import Dict

from pydantic import BaseModel, Field, HttpUrl


class Config(BaseModel):
    format: str = Field(default="bestaudio/best", alias="FORMAT")
    outtmpl: str = Field(
        default="%(extractor)s-%(id)s-%(title)s.%(ext)s", alias="OUTTMPL"
    )
    restrict_filenames: bool = Field(default=True, alias="RESTRICTFILENAMES")
    no_playlist: bool = Field(default=False, alias="NOPLAYLIST")
    no_check_certificate: bool = Field(default=True, alias="NOCHECKCERTIFICATE")
    ignore_errors: bool = Field(default=False, alias="IGNOREERRORS")
    log_to_stderr: bool = Field(default=False, alias="LOGTOSTDERR")
    quiet: bool = Field(default=True, alias="QUIET")
    no_warnings: bool = Field(default=True, alias="NO_WARNINGS")
    audio_format: str = Field(default="mp3", alias="AUDIOFORMAT")
    default_search: str = Field(default="auto", alias="DEFAULT_SEARCH")
    source_address: str = Field(default="0.0.0.0", alias="SOURCE_ADDRESS")

    before_options: str = Field(
        default="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        alias="BEFORE_OPTIONS",
    )
    options: str = Field(default="-vn", alias="OPTIONS")

    uploader: str = Field(default="Max Raabe & Palast Orchester", alias="UPLOADER")
    uploader_url: HttpUrl = Field(
        default="https://www.youtube.com/channel/UCXh3cIvGrgFnYYDV4Bzru0Q",
        alias="UPLOADER_URL",
    )
    upload_date: str = Field(default="21.11.2019", alias="UPLOAD_DATE")
    title: str = Field(
        default="Mein kleiner grüner Kaktus (MTV Unplugged)", alias="TITLE"
    )
    thumbnail: HttpUrl = Field(
        default="https://www.silvaporto.com.br/wp-content/uploads/2017/08/default_thumbnail-768x576.jpg",
        alias="THUMBNAIL",
    )
    description: str = Field(default="Beste", alias="DESCRIPTION")
    duration: int = Field(default=136, alias="DURATION")
    url: HttpUrl = Field(
        default="https://www.youtube.com/watch?v=LpEIfFuP3O4", alias="URL"
    )

    hour: int = Field(default=12, enaliasv="HOUR")

    command_prefix: str = Field(default="!", alias="COMMAND_PREFIX")

    @property
    def ytdl_format_options(self) -> Dict[str, str]:
        return {
            "format": self.format,
            "outtmpl": self.outtmpl,
            "restrict_filenames": self.restrict_filenames,
            "no_playlist": self.no_playlist,
            "no_check_certificate": self.no_check_certificate,
            "ignore_errors": self.ignore_errors,
            "log_to_stderr": self.log_to_stderr,
            "quiet": self.quiet,
            "no_warnings": self.no_warnings,
            "audio_format": self.audio_format,
            "default_search": self.default_search,
            "source_address": self.source_address,
        }

    @property
    def ffmpeg_options(self) -> Dict[str, str]:
        return {"before_options": self.before_options, "options": self.options}

    @property
    def default_info(self) -> Dict[str, str]:
        return {
            "uploader": self.uploader,
            "uploader_url": self.uploader_url,
            "upload_date": self.upload_date,
            "title": self.title,
            "thumbnail": self.thumbnail,
            "description": self.description,
            "duration": self.duration,
            "url": self.url,
        }
