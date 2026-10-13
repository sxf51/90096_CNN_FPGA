#ifndef _UTIL_H_
#define _UTIL_H_

#include <string>

#include "srcnn.h"

// load image from uint8_t file and normalize to interval [0, 1]
void load_image(std::string  fname,
                ftmap_t     *image,
                int          count);

// load feature map from single precision FLP file
void load_ftmap(std::string  fname,
                ftmap_t     *ftmap,
                int          count);

// load conv layer parameters from single precision FLP file
void load_param(std::string  fname,
                param_t     *param,
                int          count);

// returns MSE between two images
double calculate_mse(ftmap_t *img1,
                     ftmap_t *img2,
                     int      count);

// return PSNR between two images
double calculate_PSNR(ftmap_t *img1,
					  ftmap_t *img2,
					  int      count);

// write ftmap image to output file
void write_bin(std::string    fname,
			   ftmap_t       *ftmap,
			   int            count);

#endif
