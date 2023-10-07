path=/data2/jose/corpus/tablas_DU/icdar_488/fold_1/train_dev_data
python3.6 prepare/remove_special_chars.py --path_syms ${path}/syms_tr \
--path_in /data2/jose/projects/HTR/prepare/char.tr.txt \
--path_out /data2/jose/projects/HTR/prepare/text.txt