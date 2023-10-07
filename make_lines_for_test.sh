folds=(1 2 3 4)
for fold in "${folds[@]}"; do
path=/data2/jose/corpus/tablas_DU/icdar_488/fold_${fold}
time python3.6 prepare/make_lines.py --threads 4 --ext_images jpg \
--path_input ${path}/test \
--path_out ${path}/test_data \
--fname_table table_te.txt \
--fname_trans_map syms_tr_del \
--dir_output_lines lines_te \
--fname_trans trans_te.txt \
--min_size 20 30 \
--rotate True --angle_rot 90 --ratio_rotate 0.5 \
--do_img True

rm ${path}/test/syms_tr_del
done
##PASAU
# time python3.6 prepare/make_lines.py --threads 4 --ext_images jpg \
# --path_input /data2/jose/corpus/German-Parish-Records/train_dev_data/tr_data \
# --path_out /data2/jose/corpus/German-Parish-Records/train_dev_data/ \
# --fname_table table_tr.txt \
# --fname_trans_map syms_tr \
# --dir_output_lines lines_tr \
# --fname_trans_map trans_tr.txt \
# --min_size 15 15 \
# --rotate True --angle_rot 0 --ratio_rotate 1000 \
# --do_img False --passau True

# time python3.6 prepare/make_lines.py --threads 4 --ext_images jpg \
# --path_input /data2/jose/corpus/German-Parish-Records/train_dev_data/dev_data \
# --path_out /data2/jose/corpus/German-Parish-Records/train_dev_data/ \
# --fname_table table_dev.txt \
# --fname_trans_map syms_dev \
# --fname_trans_map trans_tr.txt \
# --dir_output_lines lines_dev \
# --fname_trans_map trans_dev.txt \
# --min_size 15 15 \
# --rotate False --angle_rot 0 --ratio_rotate 1000 \
# --do_img False --passau True

# rm /data2/jose/corpus/German-Parish-Records/train_dev_data/syms_dev