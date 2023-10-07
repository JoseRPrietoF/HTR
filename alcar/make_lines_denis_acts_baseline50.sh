cd ..
nthreads=4
path=/data2/LITIS/DAN/Datasets/raw/ALCAR_denis/bls
path_out=${path}/htr_acts_bl50
mkdir ${path_out}
do_img=True
height_from_baseline=50
time python prepare/make_lines_acts.py --threads ${nthreads} --ext_images TIF \
--path_input ${path}/train/page \
--path_out ${path_out}/tr \
--fname_table table_tr.txt \
--fname_trans_map syms_tr \
--dir_output_lines lines_tr \
--fname_trans trans_tr.txt \
--min_size 5 5 \
--rotate False --angle_rot -90 \
--do_img ${do_img} --crop_baseline True --height_from_baseline ${height_from_baseline}

time python prepare/make_lines_acts.py --threads ${nthreads} --ext_images TIF \
--path_input ${path}/val/page \
--path_out ${path_out}/val \
--fname_table table_val.txt \
--fname_trans_map syms_dev \
--fname_trans trans_val.txt \
--dir_output_lines lines_val \
--min_size 5 5 \
--rotate False --angle_rot -90 \
--do_img ${do_img} --crop_baseline True --height_from_baseline ${height_from_baseline}

# rm ${path}/syms_dev

time python prepare/make_lines_acts.py --threads ${nthreads} --ext_images TIF \
--path_input ${path}/test/page \
--path_out ${path_out}/te \
--fname_table table_test.txt \
--fname_trans_map syms_dev \
--fname_trans trans_test.txt \
--dir_output_lines lines_test \
--min_size 5 5 \
--rotate False --angle_rot -90 \
--do_img ${do_img} --crop_baseline True --height_from_baseline ${height_from_baseline}

##For table of syms
time python prepare/make_lines_acts.py --threads ${nthreads} --ext_images TIF \
--path_input ${path}/trainval/page \
--path_out ${path_out}/trainval \
--fname_table table_val.txt \
--fname_trans_map syms_dev \
--fname_trans trans_val.txt \
--dir_output_lines lines_val \
--min_size 5 5 \
--rotate False --angle_rot -90 \
--do_img ${do_img}

rm ${path}/syms_dev
cd alcar