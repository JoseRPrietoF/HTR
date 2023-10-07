cd ..
path=/data2/jose/corpus/tablas_DU/icdar19_headers/page
time python prepare/make_lines.py --threads 4 --ext_images jpg \
--path_input ${path}/train \
--path_out ${path}/lines/tr \
--fname_table table_tr.txt \
--fname_trans_map syms_tr \
--dir_output_lines lines_tr \
--fname_trans trans_tr.txt \
--min_size 5 5 \
--rotate True --angle_rot -90 \
--do_img True

time python prepare/make_lines.py --threads 4 --ext_images jpg \
--path_input ${path}/val \
--path_out ${path}/lines/val \
--fname_table table_val.txt \
--fname_trans_map syms_dev \
--fname_trans trans_val.txt \
--dir_output_lines lines_val \
--min_size 5 5 \
--rotate True --angle_rot -90 \
--do_img True

# rm ${path}/syms_dev

time python prepare/make_lines.py --threads 4 --ext_images jpg \
--path_input ${path}/test \
--path_out ${path}/lines/te \
--fname_table table_test.txt \
--fname_trans_map syms_dev \
--fname_trans trans_test.txt \
--dir_output_lines lines_test \
--min_size 5 5 \
--rotate True --angle_rot -90 \
--do_img True

rm ${path}/syms_dev

cd make_lines