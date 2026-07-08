import cv2
import numpy as np
import glob

# =========================
# CONFIGURAÇÕES
# =========================

# Número de cantos internos do tabuleiro
CHESSBOARD_SIZE = (6, 9)

# Tamanho real de cada quadrado (em metros, mm, etc.)
SQUARE_SIZE = 0.025

# Pasta contendo as imagens da calibração
IMAGE_PATHS = glob.glob("calibration_images/*.jpg")

# Critério de refinamento
criteria = (
    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
    5000,
    0.000001
)

# =========================
# PONTOS 3D DO TABULEIRO
# =========================

objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)

objp[:, :2] = np.mgrid[
    0:CHESSBOARD_SIZE[0],
    0:CHESSBOARD_SIZE[1]
].T.reshape(-1, 2)

objp *= SQUARE_SIZE

# Vetores finais
objpoints = []
imgpoints = []

# =========================
# LEITURA DAS IMAGENS
# =========================



for fname in IMAGE_PATHS:

    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detecta chessboard
    ret, corners = cv2.findChessboardCorners(
        gray,
        CHESSBOARD_SIZE,
        None
    )

    if ret:

        objpoints.append(objp)

        # Refina precisão subpixel
        corners2 = cv2.cornerSubPix(
            gray,
            corners,
            (11, 11),
            (-1, -1),
            criteria
        )

        imgpoints.append(corners2)

        # Visualização
        cv2.drawChessboardCorners(
            img,
            CHESSBOARD_SIZE,
            corners2,
            ret
        )

        cv2.imshow("Corners", img)
        cv2.waitKey(300)

cv2.destroyAllWindows()

# =========================
# CALIBRAÇÃO
# =========================

ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
    objpoints,
    imgpoints,
    gray.shape[::-1],
    None,
    None
)

# =========================
# RESULTADOS
# =========================

print("\n=== CAMERA MATRIX ===")
print(camera_matrix)

print("\n=== DISTORTION COEFFICIENTS ===")
print(dist_coeffs)

# =========================
# SALVAR
# =========================

np.save("camera_matrix.npy", camera_matrix)
np.save("dist_coeffs.npy", dist_coeffs)

print("\nArquivos salvos.")