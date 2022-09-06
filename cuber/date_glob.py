# ISO 8601
class DateGlob:
    """Create glob pattern based of ISO date strings

    Examples
    --------

    >>> globexp = DateGlob("%Y-%m-%d")
    >>> files = list(file_dir.rglob(f"*{globexp.pattern}*.{file_ext}"))
    >>> if len(files) == 0:
    >>>     raise FileNotFoundError(
    >>>         f"No files found in '{str(file_dir)}' with date '{date_expression}'"
    >>>     )

    >>> regexp = fr"{globexp.pattern}*|$"

    >>> dates = [
    >>>     datetime.strptime(re.search(regexp, str(f)).group(), date_expression)
    >>>     for f in files
    >>> ]

    """

    def __init__(self, datestr) -> None:
        self.datestr = datestr
        self.__Y = "[0-9]" * 4
        self.__m = "[0-9]" * 2
        self.__d = "[0-9]" * 2
        self.__j = "[0-9]" * 3
        self.pattern = self.__parse_date()

    def __parse_date(self):
        self.__pattern = self.datestr
        if "%Y" in self.datestr:
            self.__replace_year()
        if "%m" in self.__pattern:
            self.__replace_month()
        if "%d" in self.__pattern:
            self.__replace_day()
        if "%j" in self.__pattern:
            self.__replace_julian()
        return self.__pattern

    def __replace_year(self):
        self.__pattern = self.__pattern.replace("%Y", self.__Y)

    def __replace_month(self):
        self.__pattern = self.__pattern.replace("%m", self.__m)

    def __replace_day(self):
        self.__pattern = self.__pattern.replace("%d", self.__d)

    def __replace_julian(self):
        self.__pattern = self.__pattern.replace("%j", self.__j)
