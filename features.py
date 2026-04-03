from scipy.spatial import distance as dist
def calculate_ear(eye_points):


    A = dist.euclidean(eye_points[1], eye_points[5])
    B = dist.euclidean(eye_points[2], eye_points[4])

    C = dist.euclidean(eye_points[0], eye_points[3])
    if C == 0:
        return 0
    ear = (A + B) / (2.0 * C)
    return ear
def calculate_mar(mouth_points):
   
    A = dist.euclidean(mouth_points[1], mouth_points[7]) 
    A2 = dist.euclidean(mouth_points[2], mouth_points[6])
    A3 = dist.euclidean(mouth_points[3], mouth_points[5])
    
 
    B = dist.euclidean(mouth_points[0], mouth_points[4]) 
    if B == 0:
        return 0
    mar = (A + A2 + A3) / (3.0 * B)
    return mar
