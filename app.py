# 下記のサイトを参考に作成
# https://welovepython.net/streamlit-folium/
import streamlit as st                      # streamlit
from streamlit_folium import st_folium      # streamlitでfoliumを使う
import folium                               # folium
import pandas as pd
from pyproj import CRS
from pyproj import Transformer

def main():
    # ページ設定
    st.set_page_config(
        page_title="国土基本図郭を見つけるサイト",
        layout="wide"
    )

    '''
    # 国土基本図郭を見つけるサイト
    
    国土基本図郭については、
    [空間情報俱楽部](https://club.informatix.co.jp/?p=1293)を参照ください。
    '''
    # 平面直角座標系（JGD2011）の EPSGコードを返す関数
    def get_epsgXY_2011(kei: int) -> int:
        return kei + 6668

    # このアプリでは最大で13系まで扱います
    max_system = 13
    # 系の数字
    numbers = list(range(1, max_system + 1))
    # 系の数字の文字
    systems = [str(n) for n in numbers]    

    # 各座標系の中心点の緯度経度の配列。13系まで。0系は無いので, [0, 0]としてある。
    centers = [[0, 0], [33, 129.5], [33, 131.0], [36, 132.17], [33, 133.5], [36, 134.33], [36, 136.0], [36, 137.17], [36, 138.5], [36, 139.83], [40, 140.83], [44, 140.25], [44, 142.25], [44, 144.25]]

    selected_system = st.sidebar.selectbox('平面直角座標系',systems)

    kei = int(selected_system)
     
    crs_4326 = CRS.from_epsg(4326) # 変換先の空間参照系はWGS1984の緯度経度
    # 変換元の空間参照系を平面直角座標系の数字から設定する
    crs_dst = CRS.from_epsg(get_epsgXY_2011(kei))
    # 変換器の設定
    transformer = Transformer.from_crs(crs_dst, crs_4326)

    # 南北、東西方向の位置を示すために、A から始まるアルファベットの配列を作成する。平面直角座標系は南北20区画東西8区画に区分される
    l_ycode = []
    for i in range(20):
        y_code = chr(65 + i)
        #print(y_code)
        l_ycode.append(y_code)

    l_xcode = []
    for i in range(8):
        x_code = chr(65 + i)
        l_xcode.append(x_code)

    # データフレームの準備
    # 50000レベル図郭の情報を格納するデータフレームの作成
    cols = ['name', 'nwcorner_x', 'nwcorner_y', 'center_x', 'center_y','lon','lat']

    df = pd.DataFrame(index=[],columns=cols)

    nw_origin_x = -160000
    nw_origin_y = 300000 
    nw_center_x = nw_origin_x + 20000
    nw_center_y = nw_origin_y - 15000

    for iy in range(0, 20):
        center_y = nw_center_y - 30000 * iy
        nwcorner_y = nw_origin_y - 30000 * iy
        for ix in range(0, 8):
            # code = f'{kei:02}' + l_ycode[iy] + l_xcode[ix]
            code = f'{kei:02}' + l_ycode[iy] + l_xcode[ix]
            center_x = nw_center_x + 40000 * ix
            nwcorner_x = nw_origin_x + 40000 * ix
            lat,lon = transformer.transform(center_y, center_x)
            #new_data = [[code, center_x, center_y, lon, lat]]
            new_data = [[code, nwcorner_x, nwcorner_y, center_x, center_y, lon, lat]]

            df_newrow = pd.DataFrame(new_data,columns=cols)
            # concatにより新たな行を追加
            df = pd.concat([df, df_newrow], axis=0)

    maps50k = df['name']
    codes_50k = maps50k.values.tolist()
    selected_50k_code = st.sidebar.selectbox('50000図郭一覧',codes_50k)
    st.sidebar.write('50000図郭を選択したらチェックボックスをチェックしてください。5000図郭が表示されます。')

    # 地図の中心の緯度/経度、タイル、初期のズームサイズを指定します。
    m = folium.Map(
        # 地図の中心位置の指定
        location= centers[kei], 
        # タイル、アトリビュートの指定
        tiles='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
        attr='平面直角座標系の図郭中心',
        # ズームを指定
        zoom_start=8
    )

    # 読み込んだデータ(緯度・経度、ポップアップ用文字、アイコンを表示)
    for i, row in df.iterrows():
        # ポップアップの作成(図郭名)
        pop= row['name']
        folium.Marker(
            # 緯度と経度を指定
            location=[row['lat'], row['lon']],
            # ツールチップの指定
            tooltip=row['name'],
            # ポップアップの指定
            popup=folium.Popup(pop, max_width=300),
            # アイコンの指定(アイコン、色)
            icon=folium.Icon(icon="home",icon_color="white", color="red")
        ).add_to(m)

    st_data = st_folium(m, width=400, height=400)

    # もし、レベル5000図郭表示がチェックされたら
    if st.sidebar.checkbox('レベル5000図郭表示'):
        st.sidebar.write(selected_50k_code)
        nw_origin50k_x, nw_origin50k_y = df[df['name']==selected_50k_code]['nwcorner_x'].iloc[-1], df[df['name']==selected_50k_code]['nwcorner_y'].iloc[-1]
        lat_center50k, lon_center50k = df[df['name']==selected_50k_code]['lat'].iloc[-1], df[df['name']==selected_50k_code]['lon'].iloc[-1]
        # st.sidebar.write(f'{lon_center50k: .4f}')
        # st.sidebar.write(f'{lat_center50k: .4f}')

        df5k = pd.DataFrame(index=[],columns=cols)
        for iy in range(0, 10):
            nwcorner_y = nw_origin50k_y - 3000 * iy
            center_y = nwcorner_y - 1500
            for ix in range(0, 10):
                code = selected_50k_code + str(iy) + str(ix)
                nwcorner_x = nw_origin50k_x + 4000 * ix
                center_x = nwcorner_x + 2000
                lat,lon = transformer.transform(center_y, center_x)
                new_data = [[code, nwcorner_x, nwcorner_y, center_x, center_y, lon, lat]]
                df_newrow = pd.DataFrame(new_data,columns=cols)
                df5k = pd.concat([df5k, df_newrow], axis=0)

        m2 = folium.Map(
            # 地図の中心位置の指定
            location= [lat_center50k, lon_center50k], 
            # タイル、アトリビュートの指定
            tiles='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
            attr= selected_50k_code,
            # ズームを指定
            zoom_start=10
        )

        # マーカープロット
        for i, row in df5k.iterrows():
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=row['name'],
                icon=folium.Icon(color='red')
            ).add_to(m2)

        st_data = st_folium(m2, width=400, height=400)

        # 5000図郭のセレクトボックスを表示する
        maps5k = df5k['name']
        codes_5k = maps5k.values.tolist()
        selected_5k_code = st.sidebar.selectbox('5千図郭一覧',codes_5k)
        st.sidebar.write('5000図郭を選択したらチェックボックスをチェックしてください。2500図郭が表示されます。')


    if st.sidebar.checkbox('レベル2500図郭表示'):
        #st.sidebar.write(selected_5k_code)
        nw_origin5k_x, nw_origin5k_y = df5k[df5k['name']==selected_5k_code]['nwcorner_x'].iloc[-1], df5k[df5k['name']==selected_5k_code]['nwcorner_y'].iloc[-1]
        lat_center5k, lon_center5k = df5k[df5k['name']==selected_5k_code]['lat'].iloc[-1], df5k[df5k['name']==selected_5k_code]['lon'].iloc[-1]
        # st.sidebar.write(f'{lon_center5k: .4f}')
        # st.sidebar.write(f'{lat_center5k: .4f}')

        # ポリゴン描画用に東西南北の緯度経度の列を追加する
        corner_cols = ['nw_lon', 'nw_lat', 'ne_lon', 'ne_lat', 'se_lon', 'se_lat', 'sw_lon','sw_lat']
        cols2500=cols + corner_cols
        #2500レベルのデータベースの作成

        df2500 = pd.DataFrame(index=[],columns=cols2500)
        # 5000レベル図郭の中心点の緯度経度の取得
        #lat_center5k, lon_center5k = df5k[df5k['name']==selected_5k_code]['lat'].iloc[-1], df5k[df5k['name']==selected_5k_code]['lon'].iloc[-1]

        # 4分割図郭のオフセット値の定義
        l_offset2500 = [[0, 0], [2000, 0], [0, -1500],[2000, -1500]]

        # 2500レベル図郭のデータベースの構築
        for i in range(0, 4):
            nwcorner_x = nw_origin5k_x + l_offset2500[i][0]
            nwcorner_y = nw_origin5k_y + l_offset2500[i][1]
            code = selected_5k_code + str(i+1)
            center_x, center_y = nwcorner_x + 1000, nwcorner_y - 750
            lat,lon = transformer.transform(center_y, center_x)
            # 東西南北単の座標を緯度経度に変換
            nw_lat, nw_lon = transformer.transform(center_y + 750, center_x - 1000)
            ne_lat, ne_lon = transformer.transform(center_y + 750, center_x + 1000)
            se_lat, se_lon = transformer.transform(center_y - 750, center_x + 1000)
            sw_lat, sw_lon = transformer.transform(center_y - 750, center_x - 1000)
            new_data = [[code, nwcorner_x, nwcorner_y, center_x, center_y, lon, lat, nw_lon, nw_lat, ne_lon, ne_lat, se_lon, se_lat, sw_lon, sw_lat]]
            #new_data = [[code, nwcorner_x, nwcorner_y, center_x, center_y, lon, lat]]
            df_newrow = pd.DataFrame(new_data,columns=cols2500)
            df2500 = pd.concat([df2500, df_newrow], axis=0)

        # 2500レベル図郭描画用のマップの設定
        m3 = folium.Map(
            # 地図の中心位置の指定
            location= [lat_center5k, lon_center5k], 
            # タイル、アトリビュートの指定
            tiles='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
            attr= selected_5k_code,
            # ズームを指定
            zoom_start=13
        )

        # マーカープロット
        # for i, row in df2500.iterrows():
        #     folium.Marker(
        #         location=[row['lat'], row['lon']],
        #         popup=row['name'],
        #         icon=folium.Icon(color='red')
        #     ).add_to(m3)

        for i, row in df2500.iterrows():
            nw, ne, se, sw = (row['nw_lat'], row['nw_lon']), (row['ne_lat'], row['ne_lon']), (row['se_lat'], row['se_lon']), (row['sw_lat'], row['sw_lon'])
            corners = [nw, ne, se, sw]
            folium.Polygon(
                locations = corners,
                popup = row['name'],
                color="red", # 線の色
                weight=3, # 線の太さ
                fill=True, # 塗りつぶす
                #fill_opacity=0.1 # 透明度（1=不透明）
            ).add_to(m3)

        st_data = st_folium(m3, width=400, height=400)

            # 5000図郭のセレクトボックスを表示する
            # maps5k = df5k['name']
            # codes_5k = maps5k.values.tolist()
            # selected_5k_code = st.sidebar.selectbox('5千図郭一覧',codes_5k)

if __name__ == '__main__':
    main()

