import cv2
import numpy as np
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

#############################################################
######## THIẾT ĐẶT CÁC THÔNG SỐ THEO NHU CẦU THỰC TẾ ########
#############################################################

# Khung đo vận tốc (pixel): thứ tự góc phần tư: i ii iii iv
tachometerFrame = [[[215, 90], [120, 90], [-40, 240], [135, 240]],[[285, 90], [215, 90], [135, 240], [285, 240]],[[360, 90], [285, 90], [285, 240], [440, 240]],[[430,90],[360,90],[440,240],[600,240]]]
# Chiều cao và Chiều rộng tối thiểu cho xe (pixel)
minWidth = 50
minHeight = 50
# Độ dài thực tế của khung đo vận tốc trên thực địa (mét)
actualLengthOfFrame = 5
# Tốc độ cho phép: (km/h)
speedAllows = 50
# Tọa độ của dòng kẻ đếm xe (pixel)
carCountingLine = 240
# Số khung hình trên giây FPS (khung/giây)
videoSpeed = 30  # FPS

############################################################
############## KẾT THÚC PHẦN CÀI ĐẶT THÔNG SỐ ##############
############################################################

previousCarFrame=[0,0,0,0]
# Biến dùng đếm số xe
countingCars = 0
# Biến dùng lưu tốc độ xe (km/h)
carSpeedCurrent=[0,0,0,0]
# Các khung hình trong video được đánh số thứ tự
frameOrder = 0
# Mảng danh sách khung hình khi xe bắt đầu vào khung đo tốc độ đến khi rời khỏi khung
listFrame = [[],[],[],[]]
# Mảng này lưu danh sách vị trí tất cả các xe tại 1 khung hình
carsDetection = []
# Biến lưu vận tốc của xe hiện tại hoặc xe cuối cùng được đo xong
carSpeedNew=[0,0,0,0]
positionDisplaySpeed = [(2, 280),(150, 300),(320, 300),(450, 280)]
# Lưu dữ liệu
def saveVehicleDataOverSpeed(lan_xe,thoiGianBatDauDo, tocDoXe):
    f = open("du_lieu_xe_qua_toc_do.txt", 'a')
    f.write('\nLan xe : ' + str(lan_xe))
    f.write(', Thu tu khung hinh = ' + str(thoiGianBatDauDo))
    f.write(', Toc do xe: ' + str(tocDoXe))
    f.close()

# Lấy tọa độ trung tâm của hình chữ nhật
def coordinates_central(coordinate_x, coordinate_y, width, height):
    x1 = int(width / 2)
    y1 = int(height / 2)
    cx = coordinate_x + x1
    cy = coordinate_y + y1
    return cx, cy


# Nhập video
video = cv2.VideoCapture('videoTest.mp4')
# Tạo đối tượng  nền
backgroundObject = cv2.createBackgroundSubtractorMOG2()
kernel=None
while True:
    k = cv2.waitKey(videoSpeed)
    # Đọc video
    ret, frame = video.read()

    if ret:
        # Đánh số thứ tự khung hình
        frameOrder = frameOrder + 1
        # thay đổi kích thước khung hình
        frame = cv2.resize(frame, (600,330),  interpolation = cv2.INTER_AREA)
        frameCopy = frame.copy()
        # Vẽ khung đo vận tốc
        for f in tachometerFrame:
            cv2.polylines(frameCopy, [np.array(f, np.int32)], 1, (0, 255, 255))
        # Vẽ đường kẻ tại vị trí đếm xe
        cv2.line(frameCopy, (0, carCountingLine), (600, carCountingLine), (255, 127, 0), 3)

        # theo dõi
        fgmask = backgroundObject.apply(frame)
        initialMask = fgmask.copy()
        # Thực hiện ngưỡng hình ảnh để xóa bỏ bóng của xe.
        _, fgmask = cv2.threshold(fgmask, 250, 255, cv2.THRESH_BINARY)
         # Thực hiện phương thức xói mòn để làm mỏng các đường viền giúp loại bỏ bớt các chi tiết dư thừa
        fgmask = cv2.erode(fgmask, kernel, iterations = 1)
        # Thực hiện phương thức giản nở
        fgmask = cv2.dilate(fgmask, kernel, iterations = 2)
        # Lấy danh sách các đường viền
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

       
        for (i, c) in enumerate(contours):
            # lọc các khung viền giả
            (x, y, w, h) = cv2.boundingRect(c)
            if cv2.contourArea(c)>400:
                if((w < minWidth) and (h < minHeight)):
                    continue
                (height,width,depth)=frame.shape
                if (w>=width and h >= height):
                    continue
            # xác định vị trí xe
                cv2.rectangle(frameCopy, (x, y), (x + w, y + h), (0, 255, 0), 2)
                carCenter = coordinates_central(x, y, w, h)
                cv2.circle(frameCopy, carCenter, 4, (0, 0, 255), -1)
                carsDetection.append(carCenter)

            for (x, y) in carsDetection:
                # Thêm frame vào list khi xe ở trong hình vẽ
                for i in range(len(tachometerFrame)):
                    if(Polygon(tachometerFrame[i]).contains(Point(x,y))):
                        listFrame[i].append(frameOrder)
                carsDetection.remove((x, y))
            # tính vận tốc
            for i in range(len(listFrame)):
                if len(listFrame[i]) > 1:
                    if frameOrder - max(listFrame[i]) > 1:
                        carSpeedNew[i] = ((actualLengthOfFrame * videoSpeed) * 3.6 / (max(listFrame[i]) - min(listFrame[i])))
                        previousCarFrame[i]=max(listFrame[i])
                        countingCars += 1
                        cv2.line(frameCopy, (0, carCountingLine), (600, carCountingLine), (0, 127, 255), 3)
                        listFrame[i] = []
        for i in range(len(carSpeedNew)):
            if(carSpeedNew[i]>0 and carSpeedNew[i]!=carSpeedCurrent[i]):
                carSpeedCurrent[i] = carSpeedNew[i]

        for i in range(len(carSpeedCurrent)):
            if carSpeedCurrent[i] > speedAllows:
                cv2.putText(frameCopy, str(round(carSpeedCurrent[i], 1)) + 'km/h', positionDisplaySpeed[i], cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1, cv2.LINE_AA)
            else:
                cv2.putText(frameCopy, str(round(carSpeedCurrent[i], 1)) + 'km/h', positionDisplaySpeed[i], cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1, cv2.LINE_AA)

        cv2.putText(frameCopy, 'Frame: ' + str(frameOrder), (400, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0),2, cv2.LINE_AA)
        cv2.putText(frameCopy, "So xe: " + str(countingCars), (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0),2, cv2.LINE_AA)
        
        # Lưu thông tin nếu vượt quá tốc độ cho phép
        for i in range(len(carSpeedNew)):
            if carSpeedNew[i] > speedAllows:
                if (frameOrder != previousCarFrame[i]):
                    saveVehicleDataOverSpeed(str(i+1),frameOrder, carSpeedNew[i])
                    cv2.imwrite('./image/car'+ str(frameOrder) + '.jpg', frameCopy )
                    previousCarFrame[i]=frameOrder
                    carSpeedNew[i]=0
        # Trích xuất nền trước từ khung bằng mặt nạ được phân đoạn
        foregroundPart = cv2.bitwise_and(frame, frame, mask=fgmask)
        # Video gốc
        cv2.imshow("Video goc", frame)
        # Video tương phản
        cv2.imshow("Video tuong phan chua qua xu ly", initialMask)
        cv2.imshow("Video tuong phan sau khi xu ly", fgmask)
        # Video kết quả
        cv2.imshow("Video ket qua", frameCopy)
        
    else:
        break
    if k == ord('q'):
        break
    if k == ord('t'):
        cv2.waitKey(1000000)
# Lưu dữ liệu thống kê
file = open('du_lieu_xe_qua_toc_do.txt', 'a')
file.write("\ncar: " + str(countingCars) + ', q (car/s) = ' + str(countingCars / (frameOrder / videoSpeed)))
file.close()
# Giải phóng đối tượng VideoCapture
video.release()
# Đóng cửa sổ
cv2.destroyAllWindows()
