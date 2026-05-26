import os
import cv2

save_dir = "./dataset"

frames = [1,2,3,4,5,6]

COLORS = {
    0: (0, 255, 0),   
    1: (0, 0, 255),   
}

def draw_yolo_boxes(img, labels):

    H, W = img.shape[:2]
    for cls, x, y, w, h in labels:
        x1 = int((x - w / 2) * W)
        y1 = int((y - h / 2) * H)
        x2 = int((x + w / 2) * W)
        y2 = int((y + h / 2) * H)

        x1 = max(0, min(W - 1, x1))
        y1 = max(0, min(H - 1, y1))
        x2 = max(0, min(W - 1, x2))
        y2 = max(0, min(H - 1, y2))

        color = COLORS.get(int(cls), (255, 255, 0))  
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        label_text = f"class {int(cls)}"
        # Put label above box
        cv2.putText(img, label_text, (x1, max(0, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    return img

def read_yolo_txt(txt_path):

    labels = []
    if not os.path.isfile(txt_path):
        return labels
    with open(txt_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 5:
                # Skip 
                continue
            try:
                cls = int(float(parts[0]))
                x, y, w, h = map(float, parts[1:5])
                labels.append((cls, x, y, w, h))
            except ValueError:
                # Skip 
                continue
    return labels

def main():
    for n in frames:
        img_name = f"frame_{n}.png"
        txt_name = f"frame_{n}.txt"
        img_path = os.path.join(save_dir, img_name)
        txt_path = os.path.join(save_dir, txt_name)

        if not os.path.isfile(img_path):
            print(f"[skip] image not found: {img_path}")
            continue

        img = cv2.imread(img_path)
        if img is None:
            print(f"[skip] failed to load image: {img_path}")
            continue

        labels = read_yolo_txt(txt_path)
        if len(labels) == 0:
            print(f"[info] no labels for {txt_path}, showing image without boxes.")
        else:
            print(f"[info] {len(labels)} boxes in {txt_path}")

        annotated = draw_yolo_boxes(img.copy(), labels)

        out_name = f"debug_frame_{n}.png"
        out_path = os.path.join(save_dir, out_name)
        cv2.imwrite(out_path, annotated)
        print(f"[saved] {out_path}")

        cv2.imshow(f"debug {n}", annotated)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
