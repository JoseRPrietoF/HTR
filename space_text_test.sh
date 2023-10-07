path=/data2/jose/corpus/tablas_DU/icdar_488/fold_1/test_data
path_trained=/data2/jose/corpus/tablas_DU/icdar_488/fold_1/train_dev_data
# python3.6 prepare/text_spaced.py \
# --path_res /data2/jose/corpus/tablas_DU/icdar_488/fold_1/test_data/te_trans_hyp \
# --path_out /data2/jose/corpus/tablas_DU/icdar_488/fold_1/test_data/te_trans_hyp_spaced --delimiter " " --space "<space>"
# python3.6 prepare/text_spaced.py \
# --path_res /data2/jose/corpus/tablas_DU/icdar_488/fold_1/test_data/trans_te.txt \
# --path_out /data2/jose/corpus/tablas_DU/icdar_488/fold_1/test_data/trans_te_spaced.txt --delimiter " " --space "<space>"
ngramas=(2 )
for ngram in "${ngramas[@]}"; do
python3.6 prepare/sym_to_text.py --path_syms ${path_trained}/decode${ngram}_normal/LM${ngram}/prepare_FST/words.txt \
--path_res ${path}/decode${ngram}_normal/lattices/RES \
--path_out ${path}/decode${ngram}_normal/lattices/RES_trans --syms_from_LM False
python3.6 prepare/text_spaced.py \
--path_res ${path}/decode${ngram}_normal/lattices/RES_trans \
--path_out ${path}/decode${ngram}_normal/lattices/RES_trans_spaced --delimiter " " --space "<space>"
done