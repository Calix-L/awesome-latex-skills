# Sample Paper Analysis

**Title**: Efficient Attention Mechanisms for Real-Time Object Detection

**Authors**: Wang, Li, Chen — Tsinghua University | CVPR 2024

## Abstract

Real-time object detection remains challenging for edge deployment. We propose SparseFormer, which replaces dense self-attention with sparse top-k selection, achieving 10x inference speedup while maintaining 92.3% mAP on COCO. The key insight is that most attention weights are near-zero and can be pruned without quality loss.

## 1. Introduction

Object detection has advanced rapidly with transformer architectures. However, the quadratic complexity of self-attention limits deployment on resource-constrained devices. We propose SparseFormer, which dynamically selects the top-k most relevant tokens for each query, reducing attention complexity from O(n^2) to O(nk).

## 2. Method

SparseFormer has three components:
1. Token importance scorer (lightweight MLP)
2. Top-k token selector (differentiable via straight-through estimator)
3. Sparse attention module (standard attention on selected tokens only)

Key equation: Attention(Q, K_topk, V_topk) = softmax(Q * K_topk^T / sqrt(d)) * V_topk

## 3. Experiments

| Method | COCO mAP | FPS (V100) | FPS (Jetson) |
|--------|----------|------------|--------------|
| DETR | 42.0 | 28 | 3 |
| Deformable DETR | 46.2 | 42 | 8 |
| SparseFormer (ours) | 45.8 | 286 | 31 |

Ablation: removing token scorer drops mAP by 2.1 points.

## 4. Conclusion

We presented SparseFormer for real-time detection. Future work includes extending to video and 3D detection.
