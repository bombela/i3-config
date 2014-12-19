exec rofi \
	-key-window mod1+Tab \
	-key-run Mod4-d \
	-key-workspaces Mod4-Tab \
	-modi "window,run,workspaces:$HOME/.i3/rofi_switch_workspaces.sh" \
	-font "mono 10" -o 85 -color-enabled \
    #             'bg',     'fg',     'bgalt',  'hlbg',   'hlfg'
	-color-normal "#fdf6e3,  #002b36,  #eee8d5,  #586e75,  #eee8d5" \
	-color-urgent "#fdf6e3,  #dc322f,  #eee8d5,  #dc322f,  #fdf6e3" \
	-color-active "#fdf6e3,  #268bd2,  #eee8d5,  #268bd2,  #fdf6e3" \
	#             'background', 'border'
	-color-window "#fdf6e3,     #002b36"
