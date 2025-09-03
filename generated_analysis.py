
import sys
import os
import pandas as pd
import traceback

from dsl2code import token_code_map

def run_token_code(df, token, output_dir, save_flag):
	code = token_code_map.get(token)
	if not code:
		return f"[SKIP] Unknown token: {token}\n", save_flag
	# SAVE 토큰이면 저장 플래그 설정
	if token == "SAVE":
		return f"[OK] {token}: 저장 모드 활성화\n", True
	# 시각화 토큰이면 파일로 저장 (저장 모드일 때만)
	try:
		if 'plt.show()' in code or 'sns.' in code:
			if save_flag:
				import matplotlib.pyplot as plt
				import seaborn as sns
				plt.ioff()
				# 파일명 지정
				img_path = os.path.join(output_dir, f"{token}.png")
				# 코드에서 show()를 savefig로 대체
				exec(code.replace('plt.show()', f"plt.savefig(r'{img_path}')\nplt.close()"), {'df': df, 'plt': plt, 'sns': sns, 'pd': pd})
				return f"[OK] {token}: 시각화 결과 저장됨: {img_path}\n", save_flag
			else:
				return f"[SKIP] {token}: 저장 모드가 아니므로 시각화 생략\n", save_flag
		else:
			# 일반 코드 실행 결과 캡처
			local_vars = {'df': df, 'pd': pd}
			exec(f"__result = {code}", local_vars)
			result = local_vars['__result']
			return f"[OK] {token}:\n{str(result)}\n", save_flag
	except Exception as e:
		return f"[ERR] {token}: {e}\n{traceback.format_exc()}", save_flag

def main():
	if len(sys.argv) < 4:
		print("Usage: python generated_analysis.py <csv_path> <output_txt_path> <token1> [<token2> ...]")
		print("Note: SAVE 토큰을 포함하면 결과가 파일로 저장됩니다. 없으면 메모리에만 유지됩니다.")
		sys.exit(1)
	csv_path = sys.argv[1]
	output_txt = sys.argv[2]
	tokens = sys.argv[3:]
	output_dir = os.path.dirname(output_txt) or '.'
	os.makedirs(output_dir, exist_ok=True)
	try:
		df = pd.read_csv(csv_path)
	except Exception as e:
		print(f"[ERR] CSV 파일 읽기 실패: {e}")
		sys.exit(2)
	results = []
	save_flag = False
	for token in tokens:
		result, save_flag = run_token_code(df, token, output_dir, save_flag)
		results.append(result)
	# SAVE 토큰이 있었으면 파일 저장
	if save_flag:
		with open(output_txt, 'w') as f:
			f.writelines(results)
		print(f"분석 결과가 {output_txt}에 저장되었습니다.")
	else:
		print("저장 모드가 활성화되지 않아 파일로 저장하지 않았습니다.")
		print("결과를 확인하려면 SAVE 토큰을 추가하세요.")

if __name__ == "__main__":
	main()
