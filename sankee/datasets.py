from enum import Enum
import ee
import pandas as pd


class Dataset:
    def __init__(self, collection_name, band, labels, palette):
        """
        :param str band: The name of the image band that contains class values.
        :param dict labels: A dictionary matching class values to their corresponding labels.
        :param dict palette: A dictioanry matching class values to their corresponding hex colors.
        """
        self.collection_name = collection_name
        self.band = band
        self.labels = labels
        self.palette = palette

    def __repr__(self):
        return f"<sankee.datasets.Dataset> {self.title}" \


    @property
    def keys(self):
        return list(self.labels.keys())

    @property
    def df(self):
        """
        Return a Pandas dataframe describing the dataset parameters
        """
        return pd.DataFrame({"id": self.keys, "label": self.labels.values(), "color": self.palette.values()})

    @property
    def title(self):
        return self.collection.get("title").getInfo()

    @property
    def collection(self):
        return ee.ImageCollection(self.collection_name)

    def id(self):
        return self.collection.get("system:id").getInfo()

    def get_color(self, label):
        """
        Take a label and return the associated color from the palette.
        """
        label_key = [k for k, v in self.labels.items() if v == label][0]
        return self.palette[label_key]

    def get_images(self, max_images=20):
        """
        List the names of the first n images in the dataset collection up to max_images
        """
        img_list = []
        for img in self.collection.toList(max_images).getInfo():
            try:
                img_list.append(img["id"])
            except KeyError:
                pass

        if len(img_list) == max_images:
            img_list.append('...')
        return img_list


class datasets(Dataset, Enum):
    NLCD2016 = (
        "USGS/NLCD",
        "landcover", {
            1: "No data",
            11: "Open water",
            12: "Perennial ice/snow",
            21: "Developed, open space",
            22: "Developed, low intensity",
            23: "Developed, medium intensity",
            24: "Developed, high intensity",
            31: "Barren land (rock/sand/clay)",
            41: "Deciduous forest",
            42: "Evergreen forest",
            43: "Mixed forest",
            51: "Dwarf scrub",
            52: "Shrub/scrub",
            71: "Grassland/herbaceous",
            72: "Sedge/herbaceous",
            73: "Lichens",
            74: "Moss",
            81: "Pasture/hay",
            82: "Cultivated crops",
            90: "Woody wetlands",
            95: "Emergent herbaceous wetlands"
        }, {
            1: "#000000",
            11: "#466b9f",
            12: "#d1def8",
            21: "#dec5c5",
            22: "#d99282",
            23: "#eb0000",
            24: "#ab0000",
            31: "#b3ac9f",
            41: "#68ab5f",
            42: "#1c5f2c",
            43: "#b5c58f",
            51: "#af963c",
            52: "#ccb879",
            71: "#dfdfc2",
            72: "#d1d182",
            73: "#a3cc51",
            74: "#82ba9e",
            81: "#dcd939",
            82: "#ab6c28",
            90: "#b8d9eb",
            95: "#6c9fb8"
        })

    MODIS_LC_TYPE1 = (
        "MODIS/006/MCD12Q1",
        "LC_Type1",
        {
            1: "Evergreen conifer forest",
            2: "Evergreen broadleaf forest",
            3: "Deciduous conifer forest",
            4: "Deciduous broadleaf forest",
            5: "Mixed forest",
            6: "Closed shrubland",
            7: "Open shrubland",
            8: "Woody savanna",
            9: "Savanna",
            10: "Grassland",
            11: "Permanent wetland",
            12: "Cropland",
            13: "Urban",
            14: "Cropland and natural vegetation",
            15: "Permanent snow and ice",
            16: "Barren",
            17: "Water"
        },
        {
            1: "#086a10",
            2: "#dcd159",
            3: "#54a708",
            4: "#78d203",
            5: "#009900",
            6: "#c6b044",
            7: "#dcd159",
            8: "#dade48",
            9: "#fbff13",
            10: "#b6ff05",
            11: "#27ff87",
            12: "#c24f44",
            13: "#a5a5a5",
            14: "#ff6d4c",
            15: "#69fff8",
            16: "#f9ffa4",
            17: "#1c0dff",
        }
    )

    MODIS_LC_TYPE2 = (
        "MODIS/006/MCD12Q1",
        "LC_Type2",
        {
            0: "Water",
            1: "Evergreen conifer forest",
            2: "Evergreen broadleaf forest",
            3: "Deciduous conifer forest",
            4: "Deciduous broadleaf forest",
            5: "Mixed forest",
            6: "Closed shrubland",
            7: "Open shrubland",
            8: "Woody savanna",
            9: "Savanna",
            10: "Grassland",
            11: "Permanent wetland",
            12: "Cropland",
            13: "Urban",
            14: "Cropland and natural vegetation",
            15: "Barren",
        },
        {
            0: "#1c0dff",
            1: "#05450a",
            2: "#086a10",
            3: "#54a708",
            4: "#78d203",
            5: "#009900",
            6: "#c6b044",
            7: "#dcd159",
            8: "#dade48",
            9: "#fbff13",
            10: "#b6ff05",
            11: "#27ff87",
            12: "#c24f44",
            13: "#a5a5a5",
            14: "#ff6d4c",
            15: "#f9ffa4",
        }
    )

    MODIS_LC_TYPE3 = (
        "MODIS/006/MCD12Q1",
        "LC_Type3",
        {
            0: "Water",
            1: "Grassland",
            2: "Shrubland",
            3: "Crops",
            4: "Savannas",
            5: "Evergreen broadleaf",
            6: "Deciduous broadleaf",
            7: "Evergreen conifer",
            8: "Deciduous conifer",
            9: "Barren",
            10: "Urban"
        },
        {
            0: "#1c0dff",
            1: "#b6ff05",
            2: "#dcd159",
            3: "#c24f44",
            4: "#fbff13",
            5: "#086a10",
            6: "#78d203",
            7: "#05450a",
            8: "#54a708",
            9: "#f9ffa4",
            10: "#a5a5a5"
        }
    )

    CGLS_LC100 = (
        "COPERNICUS/Landcover/100m/Proba-V-C3/Global",
        "discrete_classification",
        {
            0: "Unknown",
            20: "Shrubs",
            30: "Herbaceous vegetation",
            40: "Cultivated",
            50: "Urban",
            60: "Bare",
            70: "Snow and ice",
            80: "Water body",
            90: "Herbaceous wetland",
            100: "Moss and lichen",
            111: "Closed forest, evergreen conifer",
            112: "Closed forest, evergreen broad leaf",
            113: "Closed forest, deciduous conifer",
            114: "Closed forest, deciduous broad leaf",
            115: "Closd forest, mixed",
            116: "Closed forest, other",
            121: "Open forest, evergreen conifer",
            122: "Open forest, evergreen broad leaf",
            123: "Open forest, deciduous conifer",
            124: "Open forest, deciduous broad leaf",
            125: "Open forest, mixed",
            126: "Open forest, other",
            200: "Ocean"
        },
        {
            0: "#282828",
            20: "#FFBB22",
            30: "#FFFF4C",
            40: "#F096FF",
            50: "#FA0000",
            60: "#B4B4B4",
            70: "#F0F0F0",
            80: "#0032C8",
            90: "#0096A0",
            100: "#FAE6A0",
            111: "#58481F",
            112: "#009900",
            113: "#70663E",
            114: "#00CC00",
            115: "#4E751F",
            116: "#007800",
            121: "#666000",
            122: "#8DB400",
            123: "#8D7400",
            124: "#A0DC00",
            125: "#929900",
            126: "#648C00",
            200: "#000080"
        }
    )

    @classmethod
    def names(cls):
        """
        Return string names of all datasets.
        """
        return [e.name for e in cls]

    @classmethod
    def get(cls, i=None):
        """
        Return object at a given index i or return all if i is none. 
        """
        if i is not None:
            return list(cls)[i]

        return [e for e in cls]
