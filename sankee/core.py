import ee
import pandas as pd
import plotly.graph_objects as go

from sankee import utils


# Same as sample change but takes a list of images and an optional label list and returns a datafame with all images sampled.
# Eventually I will replace sample_change with this, but for now I'm keeping it separate.
def sample(image_list, region, dataset=None, band=None, label_list=None, n=100, scale=None, seed=0, dropna=True):
    """
    Randomly sample values of a list of images to quantify change over time.

    :param list image_list: An list of classified ee.Image objects representing change over time.
    :param ee.Geometry region: The region to sample.
    :param geevis.datasets.Dataset dataset: A dataset to which the start and end images belong, which contains a band
    value. If a dataset is not provided, a band name must be explicity provided.
    :param str band: The name of the band of start_img and end_img that contains the class value. Not needed if a
    dataset parameter is provided.
    :param list label_list: A list of labels associated with each image in image_list. If not provided, numeric labels
    will be automatically generated starting at 0.
    :param int n: The number of sample points to extract. More points will take longer to run but generate more
    representative cover statistics.
    :param int scale: The scale to sample point statistics at. Generally, this should be the nominal scale of the
    start and end image.
    :param int seed: Random seed used to generate sample points.
    :param bool dropna: If true, samples with no class data in either image will be dropped. If false, these samples
    will be returned but may cause plotting to fail.
    :return pd.DataFrame: A dataframe in which each row represents as single sample point with the starting class
    in the "start" column and the ending class in the "end" column.
    """
    if not band:
        band = dataset.band

    if not label_list:
        label_list = [str(i) for i in range(len(image_list))]

    # Cast every element in label list to string since GEE can't handle that
    label_list = [str(x) for x in label_list]

    assert len(label_list) == len(image_list) > 1

    # Assign a label to each image from the label list
    def label_images(img, img_list):
        img_list = ee.List(img_list)

        index = img_list.indexOf(img)
        img_label = ee.List(label_list).get(index)

        indexed_img = ee.Image(img).set("label", img_label)
        img_list = img_list.set(img_list.indexOf(img), indexed_img)

        return img_list

    labeled_images = ee.ImageCollection(
        ee.List(ee.List(image_list).iterate(label_images, image_list)))

    samples = ee.FeatureCollection.randomPoints(region, n, seed)

    def extract_values(point):
        # Set the location to extract values at
        geom = point.geometry()

        def extract(img, feature):
            # Extract the cover value at the point
            cover = img.reduceRegion(ee.Reducer.first(), geom, scale).get(band)
            # Get the user-defined label that was stored in the image
            label = img.get('label')

            # Set a property where the name is the label and the value is the extracted cover
            return ee.Feature(feature).set(label, cover)

        return ee.Feature(labeled_images.iterate(extract, point))

    sample_data = samples.map(extract_values)

    data = pd.DataFrame.from_dict(
        [feat["properties"] for feat in ee.Feature(sample_data).getInfo()["features"]])

    if dropna:
        data = data.dropna()

    return data[label_list]


def sankify_data(data, dataset=None, class_labels=None, class_palette=None):
    """
    Take a dataframe of data representing classified sample points and return all parameters needed to generate a
    Sankey plot. This is done by looping through columns in groups of two representing start and end conditions and
    reformating data to match the Plotly Sankey input parameters.

    :param pd.DataFrame data: A dataframe in which each row represents as single sample point and columns represent
    classes over an arbitrary number of time periods.
    :param geevis.dataset.Dataset dataset: A dataset from which the class data was generated, containing labels and
    palettes corresponding to class values. If a dataset is not provided, class labels and a class palette must be
    provided instead.
    :param dict class_labels: A dictionary where keys are the class index values and the values are corresponding
    labels. Every class index in the sample dataset must be included in class_labels.
    :param dict class_palette: A dictionary where keys are the class index values and the values are corresponding
    colors. Every class index in the sample dataset must be included in class_palette.
    :return tuple: A tuple of values used in Sankey plotting in the following order: node labels, link labels, node
    palette, link palette, labels, source, target, and values.
    """
    # Take a dataframe with two columns representing start conditions and end conditions and return it in a new dataframe
    # for use in sankey plotting
    def sankify_group(group_data, start_index=0):
        column_list = group_data.columns.tolist()

        # Transform the data to get counts of each combination of condition
        sankey_data = group_data.groupby(
            column_list).size().reset_index(name="value")

        # Calculate normalized change from start to end condition
        sankey_data["change"] = utils.normalized_change(
            sankey_data, column_list[0], "value")

        # Get lists of unique source and target classes
        unique_source = pd.unique(
            data[column_list[0]].values.flatten()).tolist()
        unique_target = pd.unique(
            data[column_list[1]].values.flatten()).tolist()

        # Generate a unique index for each source and target
        sankey_data["source"] = sankey_data[column_list[0]].apply(
            lambda x: unique_source.index(x) + start_index)
        # Offset the target IDs by the last source class to prevent overlap with source IDs
        sankey_data["target"] = sankey_data[column_list[1]].apply(
            lambda x: unique_target.index(x) + sankey_data.source.max() + 1)

        # Assign labels to each source and target
        sankey_data["source_label"] = sankey_data[column_list[0]].apply(
            lambda i: dataset.labels[i])
        sankey_data["target_label"] = sankey_data[column_list[1]].apply(
            lambda i: dataset.labels[i])

        return sankey_data[["source", "target", "value", "source_label", "target_label", "change"]]

    dataset = utils.parse_dataset(dataset, class_labels, class_palette)

    node_labels = []
    link_labels = []
    label = []
    source = []
    target = []
    value = []
    current_index = 0

    for i in range(data.columns.size - 1):
        column_group = (range(i, i+2))
        # Select a set of start and end condition columns
        group_data = data.iloc[:, column_group]

        sankified = sankify_group(group_data, start_index=current_index)
        # The start index of the next column group will be the end index of this column group. This sets the index
        # offset to achieve that.
        current_index = sankified.target.min()

        start_label = group_data.columns[0]
        end_label = group_data.columns[1]

        # Store the column label for the source data
        node_labels += [start_label for i in range(
            len(pd.unique(sankified.source)))]

        # Generate a list of strings describing the change in each row
        for i, row in sankified.iterrows():
            if row.source_label == row.target_label:
                link_label = f"{round(row.change * 100)}% of {row.source_label} remained {row.target_label}"
            else:
                link_label = f"{round(row.change * 100)}% of {row.source_label} became {row.target_label}"
            link_labels.append(link_label)

        source_labels = utils.ordered_unique(
            sankified[["source", "source_label"]].sort_values(by="source").source_label.tolist())
        target_labels = utils.ordered_unique(
            sankified[["target", "target_label"]].sort_values(by="target").target_label.tolist())

        label += source_labels + target_labels

        source += sankified.source.tolist()
        target += sankified.target.tolist()
        value += sankified.value.tolist()

    # Store the column label for the final target data
    node_labels += [end_label for i in range(len(pd.unique(sankified.target)))]
    node_palette = [dataset.get_color(l) for l in label]
    link_palette = [dataset.get_color(i) for i in [label[j] for j in source]]

    return (node_labels, link_labels, node_palette, link_palette, label, source, target, value)


def clean(data, exclude=None, max_classes=None):
    """
    Perform some cleaning on data before plotting by excluding unwanted classes and limiting the number of classes.

    :param int max_classes: The maximum number of unique classes to include in the plot. If more classes are present,
    the unimportant classes will be omitted from the plot. If max_classes is None, no classes will be dropped.
    :param list exclude: A list of class values to remove from the plot.
    """
    if exclude:
        data = data[~data.isin(exclude)].dropna()
    if max_classes:
        data = utils.drop_classes(data, max_classes)

    return data


def plot(node_labels, link_labels, node_palette, link_palette, label, source, target, value, title=None):
    """
    Generate a Sankey plot of land cover change over an arbitrary number of time steps.
    """

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            customdata=node_labels,
            hovertemplate='%{customdata}<extra></extra>',
            label=label,
            color=node_palette
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_palette,
            customdata=link_labels,
            hovertemplate='%{customdata} <extra></extra>',
        ))])

    if title:
        fig.update_layout(
            title_text=f"<b>{title}</b>",
            font_size=14,
            title_x=0.5,
            template="seaborn"
        )

    return fig


def sankify(image_list, region, label_list=None, dataset=None, band=None, class_labels=None, class_palette=None,
            exclude=None, max_classes=None, n=100, title=None, scale=None, seed=0, dropna=True):
    """
    Perform sampling, data cleaning and reformatting, and generation of a Sankey plot of land cover change over time
    within a region.
    """
    dataset = utils.parse_dataset(dataset, band, class_labels, class_palette)
    data = sample(image_list, region, dataset, band=band, label_list=label_list,
                  n=n, scale=scale, seed=seed, dropna=dropna)
    cleaned = clean(data, exclude, max_classes)
    node_labels, link_labels, node_palette, link_palette, label, source, target, value = sankify_data(
        cleaned, dataset)
    return plot(node_labels, link_labels, node_palette, link_palette, label, source, target, value, title=title)
