from os import makedirs
from os.path import join, exists
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from .constants import VIZ_ROOT
import cv2
from tensorflow.keras.applications.resnet50 import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input
from tqdm import tqdm
from sklearn.manifold import TSNE


############################################################################
# To do: 1) resizing for the funnctions that require uniform size
#        2) handle rgb/gray images 
#        3) axis labels, plot title  
#        4) num components in eigen images
#        5) optimize mean/eigen computation
#        6) optimize std vs mean, different types of plots
#        7) object detection - plot x,y
#        8) batched feature extraction
############################################################################

class ImageDataVisualize:
# the first function is used intialize/get data in the form of images and labels.
#It also checks/looksout for the greyscale values.Also it checks whether the number of images are equal to the no of labels for naming /labelling properly.
#If it is not found an error is shown.this is used for validating the images.
#The dataset is then prepared from the dataframe by giving all the appropriate tags to the respective dataframes.Image,height,width labels.
#Thea area is then calculated from the height and width and the number of imagesare then printed out.

    def __init__(self, data, labels, boxes=None):
        self.images = data
        self.labels = labels
        self.grey_present = False
        for image in self.images:
            if image.ndim < 3 or image.shape[-1] == 1:
                self.grey_present =True
                break
        # self.images = [np.expand_dims(image, axis=2) if image.ndim < 3 else image for image in self.images]
        if len(self.images) != len(self.labels):
            raise ValueError('Number of images != Number of labels')
        self.validate_images()
        self.num_images = len(self.images)
        self.dataset = pd.DataFrame({
            'Image': self.images,
            'Height': [image.shape[0] for image in self.images] if not boxes
                        else [box[2] for box in boxes],
            'Width': [image.shape[1] for image in self.images] if not boxes
                        else [box[3] for box in boxes],
            'Label': self.labels,
        })
        self.dataset['area'] = self.dataset['Height'] * self.dataset['Width']
        print('Number of images after validation and filtering:', self.num_images)
#This function is written for saving the file(of the program) for better access and smooth running.
#it looks for the  directory where the file can be saved by applying the join function if actually it is saved.
# It looks for the directory of the file where it  can be saved (by using the join function) and if such directory doen't exist a new directory has to be made by using the makedirs function.
# the x_label and y_label are also been given their respective titles.
# the title of the plot is being labelled  by combining (formatting) the plot_type and file_name.
# the path is saved by the join fucntion which combines the directory and the file name (save_dir,file_name).
#  the title is then displayed.
    def save_or_show(self, plot, plot_type, file_name,x_label=None, y_label=None, save=True, show=False):
        if save:
            save_dir = join(VIZ_ROOT, plot_type)
            if not exists(save_dir):
                makedirs(save_dir)
            if x_label != None:
                plt.xlabel(x_label)
            if y_label != None:
                plt.ylabel(y_label)
            plt.title("{}: {}".format(plot_type, file_name))
            save_path = join(save_dir, file_name)
            plot.savefig(save_path)
        if show:
            plt.title("{}: {}".format(plot_type, file_name))
            plt.show()
        plt.clf()
# this function is used to check about the data we obtained from the images that whether or not its in the desired format or not.
# if the image type isn't in an n dimensional array format then it is discarded else it is saved.
#if the image type is in ndimensional array format then its accepted or it is discarded.
#also if the dimensions of the image <=2,then again the images are skipped/discarded.

    def validate_images(self):
        for image, label in zip(self.images, self.labels):
            if type(image) != np.ndarray:
                print('Image not a numpy array, skipping...')
                self.images.remove(image)
                self.labels.remove(label)
                continue
            elif image.ndim < 2:
                print('Image has less than 2 dimensions, skipping...')
                self.images.remove(image)
                self.labels.remove(label)
                continue
# this function is used to define the aspect_ratio of the histogram plotted.
# the aspect ratrio of the histogram plotted is the ratio of its idth to the height(ratio=width/height)
# It is commonly used  to describe the proportions of a rectangular screen.
    def aspect_ratio_histogram(self, save=True, show=False):
        aspect_ratios = self.dataset['Width'] / self.dataset['Height']
        plot = sns.histplot(aspect_ratios, bins='auto')
        self.save_or_show(plot.figure, 'aspect_ratios', 'aspect_ratios', x_label='aspect_ratios', y_label='frequency', save=save, show=show)
# In this function we segregate the areas by their categories(labels) and then take the mean per category.
#then we display those figures.

    def area_vs_category(self, save=True, show=False):
        mean_areas = self.dataset.groupby('Label')['area'].mean()
        plot = sns.barplot(x=mean_areas.index, y=mean_areas.tolist())
        self.save_or_show(plot.figure, 'area_vs_category', 'area_vs_category', x_label='category',y_label= 'area', save=save, show=show)
#In this function we take the mean of the images segregated in groups as per their labels.
#in these we then choose a matrixof datset and name them images.
# we take the mean and by rows(or columns) and standardize it.
# now we display it.
    def mean_images(self, save=True, show=False):
        groups = self.dataset.groupby('Label')
        for group in groups:
            images = group[1]['Image']
            mean_image = np.array(list(images)).mean(axis=0)
            plot = plt.imshow(mean_image/255)
            self.save_or_show(plot.figure, 'mean_images', str(group[0]), save=save, show=show)
# in this function we find the eigen values and the eigen vectors of the system through principal component analysis.
#find the mean of the eigenvectors.
#we change the dimension of the mean matrix.
#finding the eigen images by rounding off the eigen vectors and then displaying it.
    def eigen_images(self, save=True, show=False):
        groups = self.dataset.groupby('Label')
        for group in groups:
            images = group[1]['Image']
            images = np.array(list(images))
            images = images.reshape(images.shape[0], -1)
            mean, eigenVectors = cv2.PCACompute(images, mean=None, maxComponents=10)
            eigenVectors = eigenVectors.reshape(10, 28, 28)
            mean = mean.reshape(28, 28)
            for i in range(10):
                # img = np.round(((((mean/255)*2)-1 + eigenVectors[i]) + 2) / 4)
                img = np.round((eigenVectors[i] + 1)/2)
                plot = plt.imshow(img)
                self.save_or_show(plot.figure, 'eigen_images/{}'.format(group[0]), str(i), save=save, show=show)
#in this function we try to figure out the number of images in each category(labels) by aranging them in  descending order(frequency wise/no of images wise).
#we then represent it visually  by plotting barplots to show them.
    def num_images_by_category(self, save=True, show=False):
        counts = self.dataset['Label'].value_counts()
        plot = sns.barplot(x=counts.index, y=counts.tolist())
        self.save_or_show(plot.figure, 'num_images_by_category', 'bar_chart',x_label='category', y_label='No. of images', save=save, show=show)
        plot = plt.pie(counts.tolist(), labels=counts.index)
        self.save_or_show(plt, 'num_images_by_category', 'pie_chart', save=save, show=show)
#here we are tracing of plot of standard deviation versus mean.here the x-axis is the mean and y axis is the standard deviation.
# hence std is plotted as a function of the mean and hence we show the dependence of standard devaiation on mean through graph.(it might be a normal distribution plot.)
    def std_vs_mean(self, save=True, show=False):
        groups = self.dataset.groupby('Label')
        y = []
        x = []
        hue = []
        for group in groups:
            images = group[1]['Image']
            images = np.array(list(images))
            mean = images.mean()
            std = images.std()
            x.append(mean)
            y.append(std)
            hue.append(group[0])
        plot = sns.scatterplot(x=x, y=y, hue=hue, palette='viridis', legend='full')
        self.save_or_show(plot.figure, 'std_vs_mean', 'std_vs_mean_categories',x_label='mean', y_label='Std Deviation', save=save, show=show)

        means = self.dataset['Image'].apply(np.mean).to_list()
        stds = self.dataset['Image'].apply(np.std).to_list()
        labels = self.dataset['Label'].to_list()
        plot = sns.scatterplot(x=means, y=stds, hue=labels, palette='viridis', legend='full')
        self.save_or_show(plot.figure, 'std_vs_mean', 'std_vs_mean_all',x_label='mean', y_label='Std Deviation', save=save, show=show)
#In this function we are trying to use t-Distributed Stochastic Neighbor Embedding (t-SNE).
#primarily used for data exploration and visualizing high-dimensional data.
#In simpler terms, t-SNE gives you a feel or intuition of how the data is arranged in a high-dimensional space.
    def t_sne(self, batch_size=32, save=True, show=False):
        model = ResNet50(weights='imagenet', pooling=max, include_top = False)
        features_list = []
        print('Extracting features ...')
        for image in tqdm(self.images):
            if self.grey_present and (image.ndim < 3 or image.shape[-1] == 1):
                image = np.stack((image.squeeze(),)*3, axis=-1)
            image = np.expand_dims(image, axis=0) 
            image = preprocess_input(image) 
            features = model.predict(image) 
            features_reduce = features.squeeze()
            features_list.append(features_reduce)

        print('Performing t-SNE ...')
        tsne = TSNE(n_components=2).fit_transform(features_list)
        x = tsne[:, 0]
        y = tsne[:, 1]
        x = (x - np.min(x)) / np.ptp(x)
        y = (y - np.min(y)) / np.ptp(y)

        plot = sns.scatterplot(x=x, y=y, hue=self.labels, palette='viridis', legend='full')
        self.save_or_show(plot.figure, 'tsne', 'tsne', x_label='Feature X', y_label='Feature Y', save=save, show=show)
