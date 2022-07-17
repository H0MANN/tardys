import os, datetime
from astropy.io import fits
from astropy.modeling import models, fitting
import numpy as np
from terminal_interface import TerminalInterface
from taoics.tardys import config, config_mysql
import argparse,time

class Detlib():
    """
    レイヤーとしてはかなりしたのモジュールになるのでできるだけ__init__に書くことはへらしたい
    画像の計算関連のモジュール
    """
    def __init__(self):
        self.interface = TerminalInterface()
        self.sat_val = 65536

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

    def reset_frame_sub(self, rawdir):
        """
        Args:
            rawdir(str) : The path of the directory where the raw data is.

        Returns:
            list of ndarray : The list of array of the reset frame subtracted image
        """
        file_list = file_list = self.list_filename(rawdir)
        arr_list = np.array([fits.getdata(file) for file in file_list])
        sub_arr_list = [arr_list[i+1] - arr_list[0] for i in range(len(arr_list)-1)]
        print(len(sub_arr_list))
        return sub_arr_list

    ########################################################################
    ## FOWLER related
    ########################################################################

    def get_fowler(self, rawdir, rsltdir,frame_id):
        """
        Create fowler subtracted image.

        Args:
            rawdir(str) : The path of the directory where the raw data is.
            rsltdir(str) : The path of the directory where the resulting data will be.
            frame_id(str) : The name of the resulting data (except for the extensions)
        """
        arr_list, reset_frame = self.get_frames(rawdir)
        sub_arr_list = self.reset_frame_sub(arr_list, reset_frame)
        fowler_image = sub_arr_list[0]

        self.interface.mkdir(rsltdir)
        rsltpath = f'{rsltdir}{frame_id}.fits'
        fits.writeto(rsltpath, fowler_image, overwrite = True)

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

    def get_sur_time(self, exp_time, stacked_sub_arr):
        """
        Args:
            exp_time(float) : The exposure time
            sub_arr_list(list of array) : the array of the reset subtracted image (or you can use n_sur instead)

        Returns:
            ndarray : The array of sampling time from the begining of the exposure.
        """
        print(type(len(stacked_sub_arr)))
        t = np.linspace(0, exp_time, len(stacked_sub_arr)+1)[1:]
        print(t)
        return t

    def reshape_arr(self, stacked_arr, n_img, n_row, n_column):
        pixels = stacked_arr.reshape((n_img, n_row*n_column))
        y = pixels.T
        return y

    def get_fit_model(self, t, stacked_arr, n_img, n_row, n_column):
        """
        Args:
            t(ndarray) : The array of sampling time from the begining of the exposure.
            stacked(ndarray) : The array of stacked image along axis=0
            n_img(int) : The number of stacked image
            n_row(int) : The number of row of the image
            n_column(int) : The number of columns of the image
        
        Returns:
            FittableModel : The least square fit model of each pixel 

        Note:
            See Also : https://docs.astropy.org/en/stable/modeling/example-fitting-model-sets.html
                        and
                       https://astropy-cjhang.readthedocs.io/en/latest/api/astropy.modeling.fitting.LinearLSQFitter.html#astropy.modeling.fitting.LinearLSQFitter
        """
        n_models = n_row * n_column
        line = models.Polynomial1D(degree=1, n_models=n_models)
        fit = fitting.LinearLSQFitter()
        reshaped_arr = self.reshape_arr(stacked_arr, n_img, n_row, n_column)
        new_model = fit(line, x=t, y=reshaped_arr)
        return new_model

    def get_sur(self, rawdir, rsltdir, frame_id, exp_time):
        """
        Args:
            rawdir(str) : The path of the directory where the raw data is.
            rsltdir(str) : The path of the directory where the resulting data will be.
            frame_id(str) : The name of the resulting data (except for the extensions)
            exp_time(float): The exposure time
        """
        arr_list = self.reset_frame_sub(rawdir)
        stacked_sub_arr = np.stack(arr_list)
        t = self.get_sur_time(exp_time, stacked_sub_arr)
        n_img, n_row, n_column = stacked_sub_arr.shape

        model = self.get_fit_model(t, stacked_sub_arr, n_img, n_row, n_column)
        sur_image=model.param_sets[1].T.reshape((n_row, n_column))

        self.interface.mkdir(rsltdir)
        rsltpath = f'{rsltdir}{frame_id}.fits'
        fits.writeto(rsltpath, sur_image, overwrite=True)

    ########################################################################
    ## the one actually called
    ########################################################################

    def create_fits(self, rawdir, rsltdir, frame_id, exp_time):
        """
        Args:
            rawdir(str) : The path of the directory where the raw data is.
            rsltdir(str) : The path of the directory where the resulting data will be.
            frame_id(str) : The name of the resulting data (except for the extensions)
            exp_time(float): The exposure time
        """
        if self.mysql.select_status(where={"NAME": "SAMPLE_MODE"})[0]["value"] == "FOWLER":
            self.get_fowler(rawdir, rsltdir, frame_id)
        else:
            self.get_sur(rawdir, frame_id, frame_id, exp_time)
         
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
    detlib.get_sur(args.rawdir, args.rsltdir, args.frame_id, args.exp_time)