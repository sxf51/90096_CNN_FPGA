out = read_bin_file("./output.bin", [255, 255]);

% display the image
figure, imshow(out);

function out = read_bin_file(fname, size)
    % read output from C++ bin, 
    % give the size in matrix form (ie: [255 255])

    % need to transpose since matlab column major, but C++ row major
    fileID = fopen(fname);
    out = fread(fileID,size,"uint8");
    out = pagetranspose(uint8(out));
end