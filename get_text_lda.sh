path=/data2/jose/corpus/tablas_DU/icdar_488/
time python3.6 prepare/get_text_lda.py \
--path_input ${path} \
--path_out ${path} \
--result_path "all_text" --result_path_vocab "vocab" \
--min_size 15 15
