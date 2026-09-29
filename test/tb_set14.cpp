#include <iostream>
#include <string>
#include <iomanip>
#include <dirent.h>
#include <cstring>
#include "srcnn.h"
#include "util.h"

using namespace std;

ftmap_t img_LR_set14[N0][H][W];  // low resolution input image
ftmap_t img_HR_set14[N0][H][W];  // high-resolution output image
ftmap_t img_GT_set14[N0][H][W];

param_t conv1_weights_set14[N1][N0][F1][F1];
param_t conv1_biases_set14[N1];
param_t conv2_weights_set14[N2][N1][F2][F2];
param_t conv2_biases_set14[N2];
param_t conv3_weights_set14[N3][N2][F3][F3];
param_t conv3_biases_set14[N3];

// PSNR from matlab, obtained from comparing the ground truth (GT) with the software SRCNN from matlab
double software_HR_psnr[] = {
    27.9157, // baboon
    24.9898, // barbara
    26.2451, // bridge
    26.8397, // coastguard
    33.4187, // face
    27.3319, // flowers
    35.7270, // foreman
    30.8413, // lenna
    27.1209, // man
    27.9822, // monarch
    33.4745, // pepper
    29.4367, // ppt3
    27.6649  // zebra
};

// MSE from matlab, obtained from comparing ground truth (GT) with the software SRCNN from matlab.
// Follows same image order (alphabetical) as PSNR above
double software_HR_mse[] = {
0.001614016,
0.003168386,
0.002374347,
0.002068946,
0.0004541767,
0.001847464,
0.0002662348,
0.0008223037,
0.001939961,
0.001590235,
0.0004479194,
0.001137804,
0.001711344
};

int tb_set14()
{

    // load conv weights and biases
    load_param("./weights/conv1_weights_3x_flp.bin",
               &conv1_weights_set14[0][0][0][0],
               N1*N0*F1*F1);
    load_param("./weights/conv1_biases_3x_flp.bin",
               &conv1_biases_set14[0],
               N1);
    load_param("./weights/conv2_weights_3x_flp.bin",
               &conv2_weights_set14[0][0][0][0],
               N2*N1*F2*F2);
    load_param("./weights/conv2_biases_3x_flp.bin",
               &conv2_biases_set14[0],
               N2);
    load_param("./weights/conv3_weights_3x_flp.bin",
               &conv3_weights_set14[0][0][0][0],
               N3*N2*F3*F3);
    load_param("./weights/conv3_biases_3x_flp.bin",
               &conv3_biases_set14[0],
               N3);

	// run SRCNN on all images in Set14
    cout << "***** SRCNN - Set14 Test *****" << endl;

    std::string directoryPath = "./set14/";
    DIR *dir;
    struct dirent *ent;
    int i=0;

    // Open the directory
    if ((dir = opendir(directoryPath.c_str())) != nullptr) {
        // Read files from the directory

        // print headers for table
        std::cout << std::setw(15) << std::left << "Image Name"
                  << std::setw(20) << std::left << "PSNR GT vs HR (dB)"
                  << std::setw(27) << std::left << "PSNR GT vs HR MATLAB (dB)"
			      << std::setw(20) << std::left << "PSNR GT vs LR (dB)" 
                  << std::setw(15) << std::left << "MSE GT vs HR" 
                  << std::setw(27) << std::left << "MSE GT vs HR MATLAB" << std::endl;

        while ((ent = readdir(dir)) != nullptr) {
        	string filename(ent->d_name);
        	size_t LR_pos = filename.find("LR") ; // check if LR is present in the filename string

            // Skip '.' and '..' entries and 'GT' entries, only work on 'LR' entries
            if (strcmp(ent->d_name, ".") != 0 && strcmp(ent->d_name, "..") != 0 && LR_pos != string::npos) {
				load_image(directoryPath + filename, &img_LR_set14[0][0][0], N0*H*W);

				std::string GT_filename(ent->d_name);
				GT_filename.replace(LR_pos, 2, "GT");

				load_image(directoryPath + GT_filename, &img_GT_set14[0][0][0], N3*H*W);

				srcnn(img_LR_set14,
					  conv1_weights_set14,
					  conv1_biases_set14,
					  conv2_weights_set14,
					  conv2_biases_set14,
					  conv3_weights_set14,
					  conv3_biases_set14,
					  img_HR_set14);

                std::cout << std::setw(15) << std::left << filename.substr(0,(filename).find("_")) 
                    << std::setw(20) << std::left <<  calculate_PSNR(&img_GT_set14[0][0][0], &img_HR_set14[0][0][0], H*W)
                    << std::setw(27) << std::left <<  software_HR_psnr[i]
                    << std::setw(20) << std::left <<  calculate_PSNR(&img_GT_set14[0][0][0], &img_LR_set14[0][0][0], H*W) 
                    << std::setw(15) << std::left <<  calculate_mse(&img_GT_set14[0][0][0],&img_HR_set14[0][0][0],N3*H*W) 
                    << std::setw(27) << std::left <<  software_HR_mse[i] << std::endl;
                i++;
            }
        }
        // Close the directory
        closedir(dir);
    } else {
        // Error handling if unable to open the directory
        perror("Error opening directory");
        return EXIT_FAILURE;
    }
//    write_bin(" ", &img_HR[0][0][0], H*W);
	return 0;
}
