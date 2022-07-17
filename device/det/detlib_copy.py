import os, datetime
from astropy.io import fits
from astropy.modeling import models, fitting
import numpy as np
from terminal_interface import TerminalInterface
from taoics.tardys import config, config_mysql
import argparse,time
import matplotlib.pyplot as plt

class Detlib():
    """
    レイヤーとしてはかなりしたのモジュールになるのでできるだけ__init__に書くことはへらしたい
    画像の計算関連のモジュール
    """
    def __init__(self):
        self.interface = TerminalInterface()
        self.sat_val = -65536
        self.ref_pix_num=8

    ########################################################################
    ## general
    ########################################################################

    def list_filename(self, dir):
        """
        Args:
            dir(str) : The path of the directory where you want to get the file name list.

        Returns:
            list : The list of file names in ascending order.
        """
        ret = os.listdir(dir)
        file_list = [dir+f for f in ret if os.path.isfile(os.path.join(dir, f))]
        return sorted(file_list)

    def get_frames(self, rawdir):
        """
        Args:
            rawdir(str) : The path of the directory where the raw data is.

        Returns:
            ndarray : The ramp images
            ndarray : The reset frame
        """
        file_list = file_list = self.list_filename(rawdir)
        reset_frame = np.array([fits.getdata(file) for file in file_list if file.endswith("0000.fits")])
        print(np.zeros_like(reset_frame).shape)
        stacked_arr =  np.array([fits.getdata(file) for file in file_list if not file.endswith("0000.fits")])
        print(stacked_arr.shape)
        print((np.zeros_like(reset_frame).shape))
        stacked_arr = np.concatenate((np.zeros_like(reset_frame), stacked_arr))
        print(stacked_arr.shape)

        print(stacked_arr, reset_frame)
        return stacked_arr, reset_frame

    def reset_frame_sub(self, stacked_arr, reset_frame):
        """
        Args:
            rawdir(str) : The path of the directory where the raw data is.

        Returns:
            list of ndarray : The list of array of the reset frame subtracted image
        """
        stacked_sub_arr = stacked_arr - reset_frame
        return stacked_sub_arr

    def get_ref_frame(self, frame):
        """
        Args:
        """
        ref_row = np.array(np.mean(np.concatenate([frame[0:self.ref_pix_num] ,frame[-self.ref_pix_num::]], axis = 0), keepdims=True, axis = 0))
        ref_column = np.array(np.mean(np.concatenate([frame[:,0:self.ref_pix_num] ,frame[:,-self.ref_pix_num::]], axis = 1), keepdims=True, axis = 1))
        ref_frame = (ref_row + ref_column)/2
        print(ref_frame)
        return ref_frame

    def ref_pix_sub(self, frame):
        """
        Args:
            rawdir(str) : T
        """
        ref_frame = self.get_ref_frame(frame)
        ref_sub_frame = frame - ref_frame
        return ref_sub_frame

    def write_image(self, rsltdir, frame_id, image):
        """
        Write the resulting image to a file.
        Args:
            rsltdir(str) : The path of the directory that stores the resulting image
            framed_id(str) : The frame ID of the resulting image
            image(ndarray) : The resulting image
        """
        self.interface.mkdir(rsltdir)
        rsltpath = f'{rsltdir}{frame_id}.fits'
        fits.writeto(rsltpath, image, overwrite = True)

    def calc_weights(self, stacked_arr):
        """
        Args:
            stacked array(ndarray) : The array of reset frame NOT subtracted images
        
        Returns:
            ndarray : The array of the weights for the LSQ fitting.
        """
        weights = (stacked_arr != self.sat_val)
        #参照ピクセルはつねに重み1(もっと効率のいい書き方はないものか)
        weights[:self.ref_pix_num] = True
        weights[-self.ref_pix_num:] = True
        weights[:,:self.ref_pix_num] = True
        weights[:,-self.ref_pix_num:] = True
        return weights

    def get_hot_pixel(self, weights):
        """
        Args:
            weights(ndarray): The array of weights

        Returns:
            ndarray : The hot pixel map
        """
        hot_pixel_map = np.where(np.sum(weights, axis=0)==0, 1, 0)
        return hot_pixel_map


    ########################################################################
    ## FOWLER related
    ########################################################################

    def get_fowler(self, rawdir):
        """
        Create fowler subtracted image.

        Args:
            rawdir(str) : The path of the directory where the raw data is.
            rsltdir(str) : The path of the directory where the resulting data will be.
            frame_id(str) : The name of the resulting data (except for the extensions)
        """
        stacked_arr, reset_frame = self.get_frames(rawdir)
        stacked_sub_arr = self.reset_frame_sub(stacked_arr, reset_frame)
        fowler_image = stacked_sub_arr[0]

        #self.write_image(rsltdir, frame_id, fowler_image)
        return fowler_image

    ########################################################################
    ## SUR related
    ########################################################################
    
    #こいつは一時的メソッド
    """
    def ramp_sub(self, rawdir, frame_id):
        sub_arr_list = self.reset_frame_sub(rawdir)
        self.interface.mkdir(f'{rawdir}/cds_sub')
        for i in range(len(sub_arr_list)):
            fits.writeto(f"{rawdir}cds_sub/{frame_id}_{i+1}.fits", sub_arr_list[i])
    """
    def get_best_fit(self, model, t, n_img, n_row, n_column):
        return model(t, model_set_axis=False).T.reshape((n_img, n_row, n_column))

    def plotramp(self, t, stacked_sub_arr, best_fit, row, col):
        plt.plot(t, stacked_sub_arr[:, row, col], '.', label=f'data pixel {row},{col}')
        plt.plot(t, best_fit[:, row, col], '-', label=f'fit to pixel {row},{col}')
        plt.xlabel('Time')
        plt.ylabel('Counts')
        plt.legend(loc='upper left')
        plt.show()

    def get_sur_time(self, exp_time, stacked_sub_arr):
        """
        Args:
            exp_time(float) : The exposure time
            sub_arr_list(list of array) : the array of the reset subtracted image (or you can use n_sur instead)

        Returns:
            ndarray : The array of sampling time from the begining of the exposure.
        """
        print(type(len(stacked_sub_arr)))
        t = np.linspace(0, exp_time, len(stacked_sub_arr))
        return t

    def reshape_arr(self, stacked_arr, n_img, n_row, n_column):
        """
        Reshape the array to conduct LSQ fitting
        Args:
            stacked_arr(ndarray):stacked array
        
        Note:
            What happens if only one data point was used to fit the line?
        """
        pixels = stacked_arr.reshape((n_img, n_row*n_column))
        y = pixels.T
        return y

    def get_fit_model(self, t, stacked_sub_arr, n_img, n_row, n_column, weights):
        """
        Args:
            t(ndarray) : The array of sampling time from the begining of the exposure.
            stacked_sub_array(ndarray) : The array of reset frame subtracted images along axis=0
            n_img(int) : The number of stacked image
            n_row(int) : The number of row of the image
            n_column(int) : The number of columns of the image
            weights(ndarray) : The array of weights (elements are either True or False)
        
        Returns:
            FittableModel : The least square fit model of each pixel 

        Note:
            If the weight include False, it may take a while to calculate the ramp image.

            See Also : https://docs.astropy.org/en/stable/modeling/example-fitting-model-sets.html
                        and
                       https://astropy-cjhang.readthedocs.io/en/latest/api/astropy.modeling.fitting.LinearLSQFitter.html#astropy.modeling.fitting.LinearLSQFitter
        """
        n_models = n_row * n_column
        line = models.Polynomial1D(degree=1, n_models=n_models)
        fit = fitting.LinearLSQFitter()
        reshaped_arr = self.reshape_arr(stacked_sub_arr, n_img, n_row, n_column)
        reshaped_weights = self.reshape_arr(weights, n_img, n_row, n_column)
        #if no pixel is saturated, set the weight to None (the calculation is much faster this way)
        if np.all(reshaped_weights==True):
            reshaped_weights = None
            print("No pixel is saturated")
        else:
            print("There are at least one satureated pixels.")

        new_model = fit(line, x=t, y=reshaped_arr, weights=reshaped_weights)
        return new_model

    def get_sur(self, rawdir, exp_time):
        """
        Args:
            rawdir(str)ame, np.array([fits.getdata(file) for file in file_list if not file.endswith("0000.fits")])])
        print(stacked_arr.shape) : The path of the directory where the raw data is.
            rsltdir(str) : The path of the directory where the resulting data will be.
            frame_id(str) : The name of the resulting data (except for the extensions)
            exp_time(float): The exposure time
        """
        stacked_arr, reset_frame = self.get_frames(rawdir)
        stacked_sub_arr = self.reset_frame_sub(stacked_arr, reset_frame)
        t = self.get_sur_time(exp_time, stacked_sub_arr)
        n_img, n_row, n_column = stacked_sub_arr.shape

        weights = self.calc_weights(stacked_arr)
        hot_pixel_map = self.get_hot_pixel(weights)
        weights = weights + hot_pixel_map #ホットピクセルは重みを1になおす()
        print(np.min(np.sum(weights, axis = 0)))
        print(self.get_hot_pixel(weights).shape)
        model = self.get_fit_model(t, stacked_sub_arr, n_img, n_row, n_column, weights)
        sur_image=model.param_sets[1].T.reshape((n_row, n_column))

        best_fit = self.get_best_fit(model, t, n_img, n_row, n_column)
        self.plotramp(t, stacked_sub_arr, best_fit, 200, 100)
        #self.write_image(rsltdir, frame_id, sur_image)
        return sur_image

    ########################################################################
    ## the one actually called
    ########################################################################

    def create_fits(self, rawdir, rsltdir, frame_id, exp_time, sample_mode):
        """
        Args:
            rawdir(str) : The path of the directory where the raw data is.
            rsltdir(str) : The path of the directory where the resulting data will be.
            frame_id(str) : The name of the resulting data (except for the extensions)
            exp_time(float): The exposure time
        """
        frame = None
        if sample_mode == "FOWLER":
            frame = self.get_fowler(rawdir)
        else:
            frame = self.get_sur(rawdir, exp_time)
        rslt_frame = self.ref_pix_sub(frame)
        self.write_image(rsltdir, frame_id, rslt_frame)
         
if __name__ == "__main__":
    detlib = Detlib()

    parser = argparse.ArgumentParser()
    parser.add_argument("rawdir")
    parser.add_argument("--rsltdir", default='/home/tardys/detector/')
    parser.add_argument("frame_id")
    parser.add_argument("--exp_time", type=int,default = 1)

    args = parser.parse_args()

    #arr_list, reset_frame = detlib.get_frames(args.rawdir)
    #print(len(arr_list), reset_frame.shape)
    detlib.create_fits(args.rawdir, args.rsltdir, args.frame_id, args.exp_time, "SUR")