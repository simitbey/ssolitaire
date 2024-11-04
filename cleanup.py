import pygame
import time

def cleanup_pygame():
    try:
        pygame.mixer.quit()
        pygame.quit()
        print("Successfully cleaned up pygame")
    except:
        print("No pygame instance to clean up")
    time.sleep(0.5)

if __name__ == "__main__":
    cleanup_pygame()