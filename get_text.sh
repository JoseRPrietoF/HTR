path=/data2/jose/corpus/tablas_DU/icdar_488/
time python prepare/get_text.py \
--path_input ${path} \
--path_out ${path} \
--result_path "all_text" --result_path_vocab "vocab" \
--min_size 15 15
