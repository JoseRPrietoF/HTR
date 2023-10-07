path=/data2/jose/corpus/tablas_DU/icdar_488/fold_1/train_dev_data
python3.6 prepare/sym_to_text.py --path_syms ${path}/decode/LM9/prepare_FST/words.txt \
--path_res ${path}/decode/lattices/RES \
--path_out ${path}/decode/lattices/RES_trans --syms_from_LM False