path=/data2/jose/corpus/tablas_DU/icdar_488/fold_1/train_dev_data
ngramas=( 1 2 3 4 5 6 7 8 9 10 15 )
for ngram in "${ngramas[@]}"; do
python3.6 prepare/sym_to_text.py --path_syms ${path}/decode${ngram}_normal/LM${ngram}/prepare_FST/words.txt \
--path_res ${path}/decode${ngram}_normal/lattices/RES \
--path_out ${path}/decode${ngram}_normal/lattices/RES_trans --syms_from_LM False
python3.6 prepare/text_spaced.py \
--path_res ${path}/decode${ngram}_normal/lattices/RES_trans \
--path_out ${path}/decode${ngram}_normal/lattices/RES_trans_spaced --delimiter " " --space "<space>"
done
# python3.6 prepare/text_spaced.py \
# --path_res ${path}/tr_dev_trans \
# --path_out ${path}/tr_dev_trans_spaced --delimiter " " --space "<space>"
# python3.6 prepare/text_spaced.py \
# --path_res ${path}/trans_tr_dev.txt \
# --path_out ${path}/trans_tr_dev_spaced.txt --delimiter " " --space "<space>"