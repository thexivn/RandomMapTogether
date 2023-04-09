from unittest import IsolatedAsyncioTestCase
from mockito import when, unstub, KWARGS
from it.thexivn.random_maps_together.client.tm_exchange_client import TMExchangeClient
from it.thexivn.random_maps_together.models.map_tag import MapTag
from it.thexivn.random_maps_together.models.api_response.api_map_info import APIMapInfo
from it.thexivn.random_maps_together.models.api_response.api_map_pack_info import APIMapPackInfo
import aiohttp
import json

class MockedResponse:
    def __init__(self, data, status):
        self.data = data
        self.status = status

    async def json(self):
        return self.data

    async def read(self):
        return json.dumps(self.data).encode("utf-8")

    def raise_for_status(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *err):
        pass

class TestTMXClient(IsolatedAsyncioTestCase):
    def setUp(self):
        self.base_url = "https://trackmania.exchange/"
        self.tmx_client = TMExchangeClient()

    def tearDown(self):
        unstub()

    async def test_get_tags(self):
        when(aiohttp.ClientSession).get(f"{self.base_url}api/tags/gettags", **KWARGS).thenReturn(MockedResponse(self._expected_map_tags(), 200))
        assert await self.tmx_client.get_tags() == self._expected_map_tags_as_objects()

    async def test_search_random_map(self):
        when(aiohttp.ClientSession).get(f"{self.base_url}api/tags/gettags", **KWARGS).thenReturn(MockedResponse(self._expected_map_tags(), 200))
        when(aiohttp.ClientSession).get(f"{self.base_url}mapsearch2/search", **KWARGS).thenReturn(MockedResponse(self._expected_map_search(), 200))
        assert await self.tmx_client.search_random_map() == APIMapInfo.from_json(self._expected_map(), self._expected_map_tags_as_objects())

    async def test_search_mappack(self):
        when(aiohttp.ClientSession).get(f"{self.base_url}mappacksearch/search", **KWARGS).thenReturn(MockedResponse(self._expected_map_pack_search(), 200))
        assert await self.tmx_client.search_mappack() == [APIMapPackInfo.from_json(self._expected_map_pack())]


    def _expected_map_search(self):
        return {
            "results": [self._expected_map()]
        }

    def _expected_map(self):
        return {
            "TrackID":101290,
            "UserID":129732,
            "Username":"Prof_Pinwheel",
            "GbxMapName":"Toybox Garden",
            "AuthorLogin":"v9utFEe5Tx6XA_axE2iU3g",
            "MapType":"TM_Race",
            "TitlePack":"TMStadium",
            "TrackUID":"VxVsErO7phpDVTPVfDaYSGb6Vrf",
            "Mood":"48x48Day",
            "DisplayCost":2827,
            "ModName":"",
            "Lightmap":8,
            "ExeVersion":"3.3.0",
            "ExeBuild":"2023-03-31_13_17",
            "AuthorTime":55008,
            "ParserVersion":2,
            "UploadedAt":"2023-04-06T10:33:33.57",
            "UpdatedAt":"2023-04-06T10:33:33.57",
            "Name":"Toybox Garden",
            "Tags":"3,21,39",
            "TypeName":"Race",
            "StyleName":"Fragile",
            "EnvironmentName":"Stadium",
            "VehicleName":"CarSport",
            "UnlimiterRequired":False,
            "RouteName":"Single",
            "LengthName":"1 min",
            "DifficultyName":"Advanced",
            "Laps":1,
            "ReplayWRID":None,
            "ReplayWRTime":None,
            "ReplayWRUserID":None,
            "ReplayWRUsername":None,
            "TrackValue":0,
            "Comments":"Welcome to Toybox Garden! Remember to play gently with your toys, or you might just break them! Happy Hunting!",
            "MappackID":0,
            "Unlisted":False,
            "Unreleased":False,
            "Downloadable":True,
            "RatingVoteCount":0,
            "RatingVoteAverage":0.0,
            "HasScreenshot":False,
            "HasThumbnail":True,
            "HasGhostBlocks":True,
            "EmbeddedObjectsCount":0,
            "EmbeddedItemsSize":12,
            "AuthorCount":1,
            "IsMP4":True,
            "SizeWarning":False,
            "AwardCount":0,
            "CommentCount":0,
            "ReplayCount":0,
            "ImageCount":0,
            "VideoCount":0
        }

    def _expected_map_pack_search(self):
        return {
            "results": [self._expected_map_pack()]
        }

    def _expected_map_pack(self):
        return {
            "ID":1952,
            "UserID":26953,
            "Username":"OregoX",
            "Name":"Miscellaneous Collection (OregoX)",
            "Description":"",
            "TypeName":"Standard",
            "StyleName":"Mixed",
            "Titlepack":"Trackmania",
            "EnvironmentName":"Stadium",
            "Unreleased":False,
            "TrackUnreleased":False,
            "TrackHidden":False,
            "TrackDownloadable":True,
            "Downloadable":True,
            "Downloads":44,
            "Request":False,
            "Created":"2022-09-20T07:14:12.043",
            "Edited":"2022-09-20T18:58:12.463",
            "VideoURL":"",
            "TrackCount":24,
            "MappackValue":0.0,
            "ShowLB":True,
            "EndDateLB":None,
            "TagsString":"1,22,27",
            "APIOn":False,
            "AutoApprove":False,
            "StandardView":None
        }

    def _expected_map_tags_as_objects(self):
        return [MapTag.from_json(map_tag_json) for map_tag_json in self._expected_map_tags()]

    def _expected_map_tags(self):
        return [
            {"ID":1,"Name":"Race","Color":""},
            {"ID":2,"Name":"FullSpeed","Color":""},
            {"ID":3,"Name":"Tech","Color":""},
            {"ID":4,"Name":"RPG","Color":""},
            {"ID":5,"Name":"LOL","Color":""},
            {"ID":6,"Name":"Press Forward","Color":""},
            {"ID":7,"Name":"SpeedTech","Color":""},
            {"ID":8,"Name":"MultiLap","Color":""},
            {"ID":9,"Name":"Offroad","Color":"705100"},
            {"ID":10,"Name":"Trial","Color":""},
            {"ID":11,"Name":"ZrT","Color":"1a6300"},
            {"ID":12,"Name":"SpeedFun","Color":""},
            {"ID":13,"Name":"Competitive","Color":""},
            {"ID":14,"Name":"Ice","Color":"05767d"},
            {"ID":15,"Name":"Dirt","Color":"5e2d09"},
            {"ID":16,"Name":"Stunt","Color":""},
            {"ID":17,"Name":"Reactor","Color":"d04500"},
            {"ID":18,"Name":"Platform","Color":""},
            {"ID":19,"Name":"Slow Motion","Color":"004388"},
            {"ID":20,"Name":"Bumper","Color":"aa0000"},
            {"ID":21,"Name":"Fragile","Color":"993366"},
            {"ID":22,"Name":"Scenery","Color":""},
            {"ID":23,"Name":"Kacky","Color":""},
            {"ID":24,"Name":"Endurance","Color":""},
            {"ID":25,"Name":"Mini","Color":""},
            {"ID":26,"Name":"Remake","Color":""},
            {"ID":27,"Name":"Mixed","Color":""},
            {"ID":28,"Name":"Nascar","Color":""},
            {"ID":29,"Name":"SpeedDrift","Color":""},
            {"ID":30,"Name":"Minigame","Color":"7e0e69"},
            {"ID":31,"Name":"Obstacle","Color":""},
            {"ID":32,"Name":"Transitional","Color":""},
            {"ID":33,"Name":"Grass","Color":"06a805"},
            {"ID":34,"Name":"Backwards","Color":"83aa00"},
            {"ID":35,"Name":"Freewheel","Color":"f2384e"},
            {"ID":36,"Name":"Signature","Color":"f1c438"},
            {"ID":37,"Name":"Royal","Color":"ff0010"},
            {"ID":38,"Name":"Water","Color":"69dbff"},
            {"ID":39,"Name":"Plastic","Color":"fffc00"},
            {"ID":40,"Name":"Arena","Color":""},
            {"ID":41,"Name":"Freestyle","Color":""},
            {"ID":42,"Name":"Educational","Color":""},
            {"ID":43,"Name":"Sausage","Color":""},
            {"ID":44,"Name":"Bobsleigh","Color":""},
            {"ID":45,"Name":"Pathfinding","Color":""},
            {"ID":46,"Name":"FlagRush","Color":"7a0000"},
            {"ID":47,"Name":"Puzzle","Color":"459873"}
        ]
