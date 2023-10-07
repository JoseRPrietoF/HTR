cd ..
path=/data/SimancasSearch
mkdir ${path}/lines/
time python prepare/make_lines.py --threads 4 --ext_images jpg \
--path_input ${path}/all \
--path_out ${path}/lines/ \
--fname_table table_tr.txt \
--fname_trans_map syms_tr \
--dir_output_lines lines_tr \
--fname_trans trans_tr.txt \
--min_size 5 5 \
--rotate False --crop_baseline True --height_from_baseline 32 --relative_to_bl True \
--top_relative_px 0 --bot_relative_px 0 \
--min_rel_height_top 5 --min_rel_height_bot 5 \
--max_rel_height_top 10 --max_rel_height_bot 10 \
--do_img True --threads 4