

# IM-CMDet: An Intramodal Enhancement and Cross-Modal Fusion Network for Small Object Detection in UAV Aerial Visible-Infrared Imagery

Minchao Luo, Rui Zhao<sup>ID</sup>, *Member, IEEE*, Shenfu Zhang, Liang Chen<sup>ID</sup>, Feng Shao<sup>ID</sup>, *Member, IEEE*, and Xiangchao Meng<sup>ID</sup>, *Senior Member, IEEE*

**Abstract**—Uncrewed aerial vehicle (UAV) aerial visible-infrared [RGB-thermal (RGBT)] object detection has been widely applied in fields such as military operations and rescue missions. However, although numerous UAV aerial RGBT object detection methods exist, several challenges remain in this field. On the one hand, drones typically operate at high altitudes, and objects only occupy a small number of pixels in imaging, posing a significant challenge to object detection. On the other hand, spatial misalignment between modalities remains a major obstacle in cross-modal fusion—especially given the small size of the objects. To address the above issues, this article proposes IM-CMDet, an intramodal enhancement and cross-modal fusion network for small object detection in UAV-based RGBT imagery, which comprises three effective modules: the detail-semantic joint enhancement (DSJE) module, the differential-based fusion weight generation (DFWG) module, and the feature reconstruction network (FRN). The DSJE module prevents small object features from being overwhelmed by background noise through optimizing feature representations across different levels. The FRN module is designed to overcome modality differences and build intermodality information correlation via the Swin-Transformer architecture. To further enhance the network's sensitivity to small objects, the DFWG combines differential and spatial attention to generate the final fusion weights while reducing the impact of background noise on detection performance. Extensive experiments on RGBTDronePerson and two additional benchmarks demonstrate that IM-CMDet achieves state-of-the-art performance through effective cross-modal fusion, significantly advancing small-object detection in complex aerial scenarios. The code is available at <https://github.com/RS-Minchao/IM-CMDet>

**Index Terms**—Aerial images, multimodal fusion, small object detection, thermal images.

Received 8 March 2025; revised 22 May 2025, 10 June 2025, 7 July 2025, and 15 September 2025; accepted 25 September 2025. Date of publication 29 September 2025; date of current version 9 October 2025. This work was supported in part by the National Natural Science Foundation of China under Grant 42301376 and Grant 42171326, in part by Zhejiang Province “Pioneering Soldier” and “Leading Goose” Research and Development Project under Grant 2023C01027, in part by Zhejiang Provincial Natural Science Foundation of China under Grant LR23D010001, in part by Ningbo Natural Science Foundation under Grant 2022J076, and in part by the Key Technology Breakthrough Plan Project of Science and Innovation Yongjiang 2035 under Grant 2024Z262. (Corresponding authors: Rui Zhao; Xiangchao Meng.)

The authors are with the Faculty of Electrical Engineering and Computer Science, Ningbo University, Ningbo, Zhejiang 315211, China (e-mail: 2311100052@nbu.edu.cn; zhaorui@nbu.edu.cn; zhangshenfu\_nbu@163.com; chenliang4@nbu.edu.cn; shaofeng@nbu.edu.cn; mengxiangchao@nbu.edu.cn).

Digital Object Identifier 10.1109/TGRS.2025.3615481

## NOMENCLATURE

|                            |                                                                      |
|----------------------------|----------------------------------------------------------------------|
| CBR                        | Convolution-batchnorm-rectified linear unit (ReLU) block.            |
| Conv( $A, B$ )             | Convolution operation with kernel $B$ on input $A$ .                 |
| $\odot$                    | Elementwise Hadamard product.                                        |
| $\cdot$                    | Broadcast-based elementwise product.                                 |
| GAP                        | Global average pooling.                                              |
| Nearest( $\cdot$ )         | Nearest-neighbor interpolation.                                      |
| SPA                        | Spatial attention mechanism.                                         |
| Linear( $\cdot$ )          | Linear projection operation.                                         |
| $I$                        | Input image.                                                         |
| $F, F_V$ , and $F_I$       | Feature pyramids extracted from input, where $F \in \{F_V, F_I\}$ .  |
| $f_V$ and $f_I$            | Feature layers from $F_V$ and $F_I$ , respectively.                  |
| $F^D, F_V^D$ , and $F_I^D$ | Output pyramids from DSJE module, where $F^D \in \{F_V^D, F_I^D\}$ . |
| $f_V^D$ and $f_I^D$        | Feature layers from $F_V^D$ and $F_I^D$ .                            |

## I. INTRODUCTION

UNMANNED aerial vehicles (UAVs) have become an important tool for rapidly acquiring ground object information due to their excellent maneuverability, wide imaging range, and low cost. They are widely used in fields such as agricultural management [1], search and rescue [2], and traffic monitoring [3]. With the development of neural networks, the performance of methods in the field of computer vision has significantly improved [4], [5], and similarly, numerous methods have emerged in UAV-based object detection [6], [7], [8]. However, despite the increasingly widespread applications of UAVs, several challenges remain, such as high-altitude imaging environments and low-light conditions. Consequently, object detection in UAV-based images continues to be an active yet challenging research task.

Conventional object detection methods are primarily designed for natural images and often fail to account for the significantly reduced size of objects in UAV-captured imagery due to high-altitude imaging conditions, leading to limited detection performance. In reality, objects in UAV images exhibit much smaller pixel dimensions compared to natural images. For categories that are inherently small in ground-level images (such as pedestrians and bicycles), their pixel areas

in UAV images may account for less than 0.1% of the entire image, which significantly increases the difficulty of detection. In the field of small object detection, several studies have addressed these challenges [9], [10], [11], [12]. For instance, Bosquet et al. [13] proposed a generative adversarial network (GAN)-based data augmentation method to mitigate the scarcity of small training samples, thereby enhancing model performance while reducing the reliance on extensive manual annotations. Zhang et al. [14] introduced a random-connection attention (RCA) module that integrates convolutional operations with attention mechanisms to jointly extract global and local features, adaptively focusing on sparse correlated regions while suppressing irrelevant background pixels. Jing et al. [15] and Ma et al. [16] improved small object detection in low-resolution UAV images through hierarchical feature fusion and a visual perception module. To address performance redundancy in existing small object extraction methods, Zhang et al. [17] further developed a wavelet-regularized channel pruning strategy, maintaining accuracy while reducing computational complexity. However, on the one hand, the aforementioned methods are insufficient in preserving information of small objects, leading to the gradual loss of small object signals as the network deepens. On the other hand, traditional object detection methods, which mostly rely on single-modality visible images, face many challenges. The imaging quality of visible images is significantly impacted by factors such as lighting variations and weather conditions, resulting in notable limitations in detection accuracy and applicability in low-visibility environments, such as rain, fog, and nighttime conditions [18]. As a result, the robustness and reliability of these single-modality methods are greatly insufficient. In contrast, thermal images have a natural advantage in low-light and adverse weather conditions [19], as they can clearly present the position and contours of objects through thermal radiation differences [9], [10]. However, thermal images lack color and detail information, unable to provide the same rich visual content as visible images. Therefore, cross-modal object detection methods that fuse visible and thermal images have gradually become a research hotspot and are widely applied in fields such as environmental monitoring [20], vehicle surveillance [21], and crowd density estimation [22]. These methods leverage the complementary advantages of both modalities to provide more robust and accurate object detection capabilities in various environments.

Based on the fusion stages of visible and thermal image fusion for object detection, related methods can be classified into pixel-level fusion [23], feature-level fusion [24], and decision-level fusion [25]. Among these fusion methods, pixel-level fusion occurs at the image layer and aims to achieve high-precision image enhancement for improved detection accuracy. However, these methods primarily focus on pixel-level relationships between images and seldom consider object semantics. When combined with object detection tasks, the fusion effect is typically constrained by detection loss, but the effectiveness of this approach remains limited [23]. Decision-level fusion uses probability distribution networks to combine multiple independent detectors and derive the final detection results by integrating their outputs. However, decision-level methods require datasets with annotations in both modalities,

which poses a challenge for their application. In contrast, feature-level fusion methods use cross-modal feature fusion strategies to explore the complex correlations between modalities, thereby achieving better performance [26], [27]. As a result, feature-level fusion methods have gradually become the mainstream research approach. Based on the fusion methods, they can further be divided into two categories: static fusion and adaptive fusion methods.

Static fusion methods, which are more commonly used in the field, achieve effective feature fusion and enhance the network's detection performance by integrating multi-modal features with reference to corresponding pixel locations through predefined architectures. For instance, Liu et al. [28] propose an object-aware adversarial learning network that learns differences while preserving commonalities between various modal features. Cao et al. [29] introduce an image observation-based pedestrian detection method that utilizes essential local information from reference modes to guide cross-modal feature aggregation. Cao et al. [30] proposed a novel lightweight fusion module that effectively integrates inputs from different modalities using channel switching and spatial attention. Zhang et al. [31], on the other hand, leverage illumination information from images to guide cross-modal feature weighting for better utilization of complementary information. However, these methods are designed for natural images without considering the unique characteristics of UAV imagery, leading to limited detection performance. Recently, UAV-based optical-infrared joint object detection technology has garnered significant attention, with numerous researchers dedicated to related endeavors [32], [33]. For aerial image object detection purposes, a cross-modal attention feature fusion module is proposed that can effectively learn shared features as well as distinguish different features within each mode in [34]. Sun et al. [26] devised an uncertainty sensing module that employs cross-modal intersections and lighting assessments to quantify the uncertainty of each object, effectively leveraging information from both modes for improved object detection outcomes. However, this method requires comprehensive annotations for both modalities, resulting in a significant annotation burden and limiting the method's adaptability. Based on an analysis of the visible and infrared spectral ranges, Jiang et al. [35] innovatively combined two out of the three RGB channels with the infrared band for feature extraction. Wang et al. [36] and Zhao et al. [37] designed a three-branch feature enhancement network to enhance the learning of features from each modality and the fused modality, introducing cross-modal attention feature fusion to fully extract shared and complementary features between the two modalities. The aforementioned method fails to account for the fact that aerial imaging results in objects occupying only a small number of pixels, making them susceptible to being overwhelmed by background features. Consequently, its performance in small object detection is constrained. To address this, Zhang et al. [38] proposed a quality-aware learning strategy to address the issue of data quality imbalance from a fine-grained perspective, thereby improving the quality of modality fusion and enhancing detection performance. Regrettably, these static fusion methods fail to consider the spatial misalignment of objects between modalities during

direct fusion, hindering the network's ability to effectively exploit the complementary information between modalities and ultimately degrading object detection performance [39].

To address the limitations of the aforementioned static fusion method Training and Testing Details, some researchers have focused on adaptive fusion, designing networks that adapt to the characteristics between different data sources in order to alleviate the weak alignment of object positions between modalities [40], [41]. To address the issues of modality calibration errors and inaccurate fusion, a new calibration complementary Transformer called C2former is proposed in [42], leveraging the powerful feature correlation learning capabilities of Transformers [43]. Despite yielding promising results, this component still imposes significant computational overhead due to the extensive use of attention mechanisms. To address the issue of limited detection performance caused by the misalignment of image pairs obtained from real-world scenarios, Song et al. [44] proposed a strategy called object search rectification, which performs registration prior to modality fusion. Although the aforementioned methods aim to reduce the modality gap through alignment operations, they place excessive emphasis on strict alignment requirements, which makes detection performance heavily dependent on the quality of the alignment. To address this, Chen et al. [45] proposed a novel method called offset-guided adaptive feature alignment, combining offset-based reference generation and deformable convolution [46]. Liu et al. [47] proposed the cross-mamba interaction and offset-guided fusion for multimodal object detection (COMO) framework, which leverages cross-Mamba interaction and offset-guided fusion to achieve efficient multimodal feature alignment and interaction for improved object detection. To address challenges from modality inconsistency and redundancy, Bao et al. [48] designed a dual-dynamic cross-modal interaction network that employs channel-gated spatial cross-attention and dynamic feature fusion. By combining deformable convolution with cross-modal global context modeling (CGC) (derived from GCNet [49]), local correction for both modes and global context learning is achieved to enhance network performance in [50]. Wang et al. [51] proposed a novel cross-scale dynamic convolution fusion module to adaptively extract and fuse bimodal features with respect to data distribution, thereby enhancing the detection performance of the method. These approaches enable the network to implicitly capture the optimal fusion locations for detection tasks, rather than relying on strict alignment. However, during high-altitude UAV operations, small objects like pedestrians and bicycles occupy less than 0.1% of total pixels, resulting in cross-modal misalignment that can reach several times the objects' own scales, significantly increasing the difficulty of feature matching. Unfortunately, the aforementioned methods fail to account for this issue, resulting in insufficient attention to small object features and the absence of a dedicated fusion strategy, ultimately limiting their performance in small object detection.

Based on the analysis of the aforementioned methods, current UAV-based RGB-thermal (RGBT) fusion methods for small object detection have several shortcomings that limit their effectiveness, which can be identified as follows.

*Issue 1:* For UAV-based RGBT object detection methods, the design does not take into account the characteristics of high-altitude imaging. Certain object categories, such as pedestrians and bicycles, occupy less than one-thousandth of the entire image, causing these discriminative features to be easily overwhelmed by background information during the network learning process.

*Issue 2:* When the object size is small, the issue of cross-modal misalignment becomes more pronounced. However, few fusion methods are specifically designed for small object detection, which may hinder the effective integration of complementary features across modalities.

To address the aforementioned issues, this article proposes a small object detection algorithm based on the fusion of UAV aerial RGBT images, termed IM-CMDet. Given a pair of visible and infrared images, initial features of each modality are independently extracted by their corresponding backbone networks. These features are, then, input into the detail-semantics joint enhancement (DSJE) module, which is devised from the feature pyramid network (FPN) [52]. In this module, high-frequency details extracted from the original images, along with high-level semantic features, are used to enhance the features at each level, enabling the long-term retention of important discriminative information. To further guide the network's attention to the hierarchical and channelwise differences in object features, DSJE introduces a new hierarchical channel attention mechanism that adjusts feature weights based on both hierarchical and channel characteristics. The enhanced features are subsequently fed into the feature reconstruction network (FRN) with an asymmetric cross-attention mechanism, specifically designed to mitigate significant misalignment in small objects, effectively reconstructing visible modality information based on infrared modality information. Finally, fusion weights, generated by combining the differential process and spatial attention from the initial features, are applied to the weighted fusion of visible and infrared modalities, reducing the impact of redundant information on detection performance while maintaining sensitivity to small object locations. This approach significantly enhances the network's performance in small object detection.

The main contributions of this article are as follows.

- 1) We propose a novel RGBT fusion network to enhance UAV-based small object detection under varying illumination conditions. By integrating discriminative feature enhancement with a cross-modal feature alignment network specifically designed for small object characteristics, our method effectively mitigates the limitations of existing small object detection approaches in this domain, leading to a significant improvement in UAV-based RGBT fusion detection performance.
- 2) To address the issue of small object features being easily overwhelmed by background information during the learning process, we design the DSJE module, which integrates semantic features with high-frequency information from the original image to enhance discriminative feature representation. Furthermore, a hierarchical channel joint attention mechanism is introduced to adaptively adjust feature representations at different levels.

![Overall framework of IM-CMDet. The diagram shows a two-stream architecture for visible (RGB) and infrared (IR) modalities. Both streams use an 'RGB Feature Extractor' or 'IR Feature Extractor' to produce feature maps $F_V$ and $F_I$. These are processed by 'DSJE' (Detail-Semantics Joint Enhancement) modules to produce $f_V^D$ and $f_I^D$. A fusion strategy is applied: $F_V$ and $F_I$ are processed by 'DFWG' (Differential-based Fusion Weight Generation Module) and 'CSOFS' (Cross-modal Small Object Feature Fusion Strategy) to generate weights $w_V$ and $w_I$. These weights are used in 'Weight Fusion' (element-wise multiplication and addition) with $F_V$ and $F_I$. The fused features are then processed by 'FRN' (Feature Reconstruction Network) to produce $f^F$. Finally, $f_V^D$, $f_I^D$, and $f^F$ are concatenated (C) and passed through 'Prehead' and 'Head' modules for detection. A 'Loss' is calculated between the 'Prehead' and 'Head' outputs. A legend at the bottom defines the symbols: (f) Weight Fusion, (⊙) Element-wise multiplication, (C) Concatenation with 1*1 conv, (+) Element-wise addition. It also defines the modules: DFWG (Differential-based Fusion Weight Generation Module), CSOFS (Cross-modal Small Object Feature Fusion Strategy), FRN (Feature Reconstruction Network), and DSJE (Detail-Semantics Joint Enhancement Module).](9e6062272bbe3ddbb7c0606721d64cf0_img.jpg)

Overall framework of IM-CMDet. The diagram shows a two-stream architecture for visible (RGB) and infrared (IR) modalities. Both streams use an 'RGB Feature Extractor' or 'IR Feature Extractor' to produce feature maps \$F\_V\$ and \$F\_I\$. These are processed by 'DSJE' (Detail-Semantics Joint Enhancement) modules to produce \$f\_V^D\$ and \$f\_I^D\$. A fusion strategy is applied: \$F\_V\$ and \$F\_I\$ are processed by 'DFWG' (Differential-based Fusion Weight Generation Module) and 'CSOFS' (Cross-modal Small Object Feature Fusion Strategy) to generate weights \$w\_V\$ and \$w\_I\$. These weights are used in 'Weight Fusion' (element-wise multiplication and addition) with \$F\_V\$ and \$F\_I\$. The fused features are then processed by 'FRN' (Feature Reconstruction Network) to produce \$f^F\$. Finally, \$f\_V^D\$, \$f\_I^D\$, and \$f^F\$ are concatenated (C) and passed through 'Prehead' and 'Head' modules for detection. A 'Loss' is calculated between the 'Prehead' and 'Head' outputs. A legend at the bottom defines the symbols: (f) Weight Fusion, (⊙) Element-wise multiplication, (C) Concatenation with 1\*1 conv, (+) Element-wise addition. It also defines the modules: DFWG (Differential-based Fusion Weight Generation Module), CSOFS (Cross-modal Small Object Feature Fusion Strategy), FRN (Feature Reconstruction Network), and DSJE (Detail-Semantics Joint Enhancement Module).

Fig. 1. Overall framework of IM-CMDet.

3) We propose a fusion strategy for cross-modal small object detection, combining differential-based fusion weight generation (DFWG) with FRN. The former enhances sensitivity to small objects and reduces redundancy, while the latter models intermodal correlations, enabling effective fusion.

The pipeline of the remaining sections of this article is as follows. In Section II, we detail the architecture of the network. In Section III, we present this work, including the experimental results and relevant comparisons to validate the effectiveness of our approach. Finally, in Section IV, we summarize and discuss this work.

## II. METHODOLOGY

### A. Overview

The overall framework of the proposed IM-CMDet is illustrated in Fig. 1. The visible and thermal modal features are extracted using a two-stream backbone network. Subsequently, the extracted features undergo processing via the DFWG to produce the necessary fusion weights for the final integration. These features are, then, fed into our proposed DSJE, which refines the extracted features from both semantic and detailed perspectives, thereby enhancing the salience of regions of interest and complementing the shallow texture features of the object. During the training phase, the enhanced features are input into the predetection head, where loss calculation optimizes the feature extraction capabilities of the preceding network stages. FRN with the asymmetric cross-window attention mechanism based on thermal modalities is

subsequently employed to augment the feature representation of visible modalities and establish correlations between the two modal objects. Finally, after adjusting the fusion weights, the weighted fusion features are input into the detection head to predict object-related information within the image.

### B. DSJE Module

As discussed, the discriminative features of small objects tend to be gradually diminished or ultimately overwhelmed by cluttered background contexts during iterative learning procedures. To address this issue, we have developed the DSJE module. This module extracts detailed features from original images and high-level semantic features, thereby enhancing the salience and representativeness of object features from both detailed and semantic perspectives. An overview of the DSJE module is provided in Fig. 2. To ensure model efficiency, we use the C3–C5 layers from the backbone network as inputs.

We obtain the initial detail information  $H$  of the image using the Laplacian operator and then generate the detail feature map through convolution operations on this initial detail information

$$\text{LAP} = \begin{bmatrix} 0 & -1 & 0 \\ -1 & 4 & -1 \\ 0 & -1 & 0 \end{bmatrix} \quad (1)$$

$$H = \text{CBR}(I, \text{LAP}) = \text{ReLU}(\text{BN}(\text{Conv}(I, \text{LAP}))) \quad (2)$$

where the  $I$  represents the initial visible or thermal image, the CBR consists of convolution, batch normalization, and

![Figure 2: Framework of DSJE module. The diagram illustrates the DSJE module's architecture. It starts with an input feature map F_V. A CBR block processes F_V to generate P_R. P_R is then upsampled and added to P_H. P_H is generated by downsampling F_V and adding it to the upsampled P_R. A High-Frequency Information Extraction block (CBR) processes P_H to generate a high-frequency information map. This map is then processed by a Layer-Channel Joint Attention block. The block consists of Global Average Pooling, Concat & FC, and a series of element-wise multiplication and addition operations. The final output is F^D. A legend at the bottom defines the symbols: 'up' for Upsampling, 'pool' for Max pooling, and a blue arrow for Convolution with stride 2.](e394c2b5c61344f6a12397f430086072_img.jpg)

Figure 2: Framework of DSJE module. The diagram illustrates the DSJE module's architecture. It starts with an input feature map F\_V. A CBR block processes F\_V to generate P\_R. P\_R is then upsampled and added to P\_H. P\_H is generated by downsampling F\_V and adding it to the upsampled P\_R. A High-Frequency Information Extraction block (CBR) processes P\_H to generate a high-frequency information map. This map is then processed by a Layer-Channel Joint Attention block. The block consists of Global Average Pooling, Concat & FC, and a series of element-wise multiplication and addition operations. The final output is F^D. A legend at the bottom defines the symbols: 'up' for Upsampling, 'pool' for Max pooling, and a blue arrow for Convolution with stride 2.

Fig. 2. Framework of DSJE module.

ReLU, and  $\text{Conv}(A, B)$  denotes the convolution of input  $A$  with kernel  $B$ .

Given the extensive coverage of UAV imagery and the high density of ground objects, edge detail features extracted using the Laplacian operator frequently contain significant noise. To mitigate the adverse effects of this noise on subsequent detection accuracy and to enhance the feature representation of regions of interest in shallow layers, this method leverages deep semantic features to generate enhanced References (ERs). Specifically, the final ER  $R$  is produced by applying convolutional operations and threshold segmentation to the deepest feature maps of the input data

$$R(x, y) = \begin{cases} K, & \text{if } \text{CBR}(f_3)(x, y) \geq T \\ 1, & \text{if } \text{CBR}(f_3)(x, y) < T \end{cases} \quad (3)$$

where  $f_3$  refers to the deepest semantic features of the input feature pyramid  $F$ ,  $(x, y)$  represents the pixel location, and  $K$  is an empirical value set to 4 here.

We subsequently upsample the ER features while downsampling the detail features to construct a feature pyramid corresponding to each layer's scale. We, then, integrate the detail feature pyramid  $P_H$  with the ER pyramid  $P_R$ , thereby generating the final detail semantic enhancement weights  $W_D$

$$P_R[i] = \text{Nearest}(R, 2^{(3-i)}), \quad i = 1, 2 \quad (4)$$

$$P_H[i] = \text{MaxPool}(H, 2^i), \quad i = 1, 2 \quad (5)$$

$$W_D = P_R + P_H \quad (6)$$

where the  $\text{Nearest}(\cdot)$  represents the nearest neighbor interpolation operation, the  $\text{MaxPool}(\cdot)$  represents the maxpooling operation, and the left side of the parentheses represents the original feature map for the operation, while the right side indicates the multiplicative factor for the operation.

Subsequently, multiply the enhanced weights by the original features of each layer to obtain the refined features  $F_e$ . Anal-

ogous to the FPN, these refined features facilitate information exchange between adjacent layers. To accommodate potentially large-scale objects, we further apply convolutional layers on the top-level features of  $F_C$  to extract deeper semantic representations

$$F_e = F \odot W \quad (7)$$

$$F_C[i] = \begin{cases} F_e[i], & \text{if } i = 3 \\ F_e[i] + \text{Nearest}(F_C[i+1], 2), & \text{if } i = 2, 1 \end{cases} \quad (8)$$

$$F_C[i] = \text{Conv}_{s=2}(F_C[i-1]), \quad i = 4, 5 \quad (9)$$

where  $\odot$  denotes the Hadamard product,  $F_C$  represents the feature after interaction, the values of  $i$  are selected in the descending order in (8), and  $\text{Conv}_{s=2}$  represents a convolution operation with a stride of 2.

Driven by the need to clearly identify the task requirements of each channel and hierarchical level, we aim to autonomously enhance the feature information of a particular layer by comparing information across different levels. Consequently, we propose a hierarchy-channel joint attention mechanism. Analogous to channel attention mechanisms, we derive hierarchical channel weights by applying GAP to the features of each channel at various levels. Subsequently, the features from each level are aggregated and processed through a fully connected layer to generate new hierarchical channel weights. These weights are, then, multiplied with the original features to obtain the refined final features  $F^D$

$$l_i = \text{GAP}(F_C[i]), \quad i = 1, 2, 3, 4, 5 \quad (10)$$

$$F^D = F_C \cdot \text{Linear}(\text{Cat}(l_1, l_2, l_3, l_4, l_5)) \quad (11)$$

where GAP denotes the global average pooling,  $\cdot$  represents the multiplication based on the broadcasting mechanism, and Cat represents the concatenation operation.

![Fig. 3. Framework of DFWG module. The diagram shows two parallel processing paths for visible (f_v) and thermal (f_t) features. Each path consists of a Spatial Attention (SPA) block, followed by a Hadamard product (circle with dot) with the original feature, then a subtraction (circle with minus) from the SPA output, and finally a CBR block to produce the fusion weight (W_v or W_t).](a7d78d22e465dea388b31d0739f9d0cd_img.jpg)

Fig. 3. Framework of DFWG module. The diagram shows two parallel processing paths for visible (f\_v) and thermal (f\_t) features. Each path consists of a Spatial Attention (SPA) block, followed by a Hadamard product (circle with dot) with the original feature, then a subtraction (circle with minus) from the SPA output, and finally a CBR block to produce the fusion weight (W\_v or W\_t).

Fig. 3. Framework of DFWG module.

### C. Cross-Modal Small Object Feature Fusion Strategy

Due to factors such as viewpoint deviation and resolution differences, there exists a positional discrepancy between objects in visible and thermal modes. Previous methods have seldom considered the size of the object when designing cross-modal feature interaction and fusion strategies. As the number of pixels occupied by the object decreases, the positional deviation becomes increasingly significant, leading to suboptimal fusion outcomes. In this article, we propose a specialized cross-modal small object feature fusion strategy (CSOFS). This strategy comprises two primary components: a difference-based fusion weight generator and an asymmetric window cross-attention-based cross-modal small-object feature alignment network.

1) *DFWG Module*: To mitigate the impact of redundant information from both modalities on the final detection accuracy, we generate fusion weights before fusion. This process aims to amplify the effective information of each modality while suppressing the expression of redundant data. Given the considerable positional deviation of small objects in UAV images across different modalities, we employ a differential approach that enables the network to emphasize object regions by leveraging significant positional deviations while simultaneously reducing background noise. This enhances the sensitivity and accuracy of the small object detection network. The detailed implementation is illustrated in Fig. 3.

The characteristics of the visible and thermal modalities are processed to generate a spatial attention mask. This mask is, then, applied to the original features through the Hadamard product, resulting in the reconstructed features. Subsequently, the reconstructed features from both modalities are combined using pixelwise subtraction to obtain the feature difference. By integrating these different results with the respective modality features, the final fusion weight  $W_{V/I}$  can be derived. Notably, to fully leverage the representational power of shallow features for small object detection, we use the C2–C5 layers extracted from the backbone network as input. The formula for this process is presented as follows:

$$w_V = \text{CBR}_{s=2} (2 (f_V) \odot \text{SPA} (f_V)) - f_t \odot \text{SPA} (f_t) \quad (12)$$

$$w_t = \text{CBR}_{s=2} (2 (f_t) \odot \text{SPA} (f_t)) - f_V \odot \text{SPA} (f_V) \quad (13)$$

![Fig. 4. Framework of FRN. The diagram shows the processing of visible (f_V^p) and thermal (f_t^p) features through CBR modules (CBR_1 and CBR_3). The features are then arranged into windows and flattened. The visible features are processed through Linear, MHCA, ADD & LN, FFN, and Rshape blocks. The thermal features are processed through a similar structure but with a shifted window. The final output is f^F.](47e8c2042061e08a14e012472e9fdbaa_img.jpg)

Fig. 4. Framework of FRN. The diagram shows the processing of visible (f\_V^p) and thermal (f\_t^p) features through CBR modules (CBR\_1 and CBR\_3). The features are then arranged into windows and flattened. The visible features are processed through Linear, MHCA, ADD & LN, FFN, and Rshape blocks. The thermal features are processed through a similar structure but with a shifted window. The final output is f^F.

Fig. 4. Framework of FRN.

where  $\text{CBR}_{s=2}$  denotes a CBR module with a convolutional stride of 2,  $\odot$  represents the Hadamard product, and SPA stands for spatial attention. The  $f_{V/I}$  is derived from the original input feature pyramid  $F_{V/I}$ .

2) *FRN Based on Small Object Correlation*: Significant positional deviations of small objects across modalities must be addressed before fusion. Some previous methods have employed feature alignment operations; however, achieving both strict and efficient feature alignment has proven challenging. Consequently, some researchers have adopted deformable convolution to enable networks to autonomously learn correlations between specific locations and other regions, thereby facilitating feature reconstruction. However, training deformable convolution remains difficult, complicating the learning of precise position offsets. Since the introduction of Transformer architectures, the attention mechanism has gained widespread adoption in computer vision. In the context of cross-modal feature interaction, cross-attention mechanisms have demonstrated considerable potential. Given that thermal modality images exhibit stable quality unaffected by illumination conditions, this study leverages a cross-attention mechanism based on thermal features to enhance the representation of visible modality features. To reduce computational burden, this method employs cross-window attention. An overview of this approach is illustrated in Fig. 4.

Due to the significant positional discrepancy between visible and thermal modalities for small- and medium-sized objects in UAV imagery, a uniformly positioned window may encompass disparate objects following window segmentation. To mitigate the adverse effects of this issue on network performance, convolutional kernels of varying dimensions are employed to extract information from the enhanced features of each modality, as illustrated in Fig. 4

$$f_V^a = \text{CBR}_{3 \times 3} (f_V^p) = \text{ReLU} (\text{BN} (\text{Conv}_{3 \times 3} (f_V^p))) \quad (14)$$

$$f_t^a = \text{CBR}_{1 \times 1} (f_t^p) = \text{ReLU} (\text{BN} (\text{Conv}_{1 \times 1} (f_t^p))) \quad (15)$$

where the  $\text{CBR}_{3 \times 3}$  represents the CBR with  $3 \times 3$  kernel size and the meaning of  $\text{CBR}_{1 \times 1}$  is similar.

To facilitate the subsequent application of local cross-attention, we partition and flatten the obtained feature map. In line with the Swin-Transformer architecture [53], the left branch employs standard window partitions, while the right branch utilizes shifted window partitions to enhance cross-window feature interaction. Specifically, the input to the left branch comprises feature maps extracted from both visible and thermal modalities, whereas the right branch processes cross-attention-enhanced visible features alongside the original thermal features. Two linear projection layers are subsequently applied separately: one to generate query vectors for the thermal image, and the other to generate keys and values for the visible features

$$Q = \text{Linear}(I_t) \quad (16)$$

$$(K, V) = \text{Linear}(I_v) \quad (17)$$

where  $I_t$  is the flattened sequence of thermal features  $f_t^a$ , and  $I_v$  is the flattened sequence of visible features  $f_v^a$ .

The generated queries, keys, and values undergo processing via multihead crossed attention (MHCA) mechanisms to conduct interactive attention computations between the visible and thermal modalities. This process enables the extraction of pertinent information across modalities, thereby enhancing the feature correlation between the two modalities and facilitating their subsequent integration

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V \quad (18)$$

$$\text{Head}_i = \text{Attention}(QW_{Qi}, KW_{Ki}, VW_{Vi}) \quad (19)$$

$$\text{MHCA}(Q, K, V) = \text{Cat}(\text{Head}_1, \dots, \text{Head}_h)W_o \quad (20)$$

where  $d_k$  is the scaling factor,  $W_{Qi}$ ,  $W_{Ki}$ , and  $W_{Vi}$  are the linear transformation matrices for each head, and  $W_o$  is the final linear transformation matrix.

The optimized features derived from the left branch, along with the original thermal features, are partitioned in the right branch via a shift window mechanism. Ultimately, the visible features  $f^F$  of the reconstructed image are extracted.

As shown in Fig. 1, after FRN optimization, the output features  $f^F$  are combined with  $f_v^D$  through residual connections to preserve the original modal information. The resulting feature is weighted by  $w_v$ , while the  $f_t^D$  is weighted by  $w_t$ , both of which are generated by the DFWG module. These two weighted feature representations are, then, concatenated and passed into the final detection head.

### D. Loss Function

To ensure the effectiveness of single-mode feature extraction when integrated with the DSJE module, we employ a dual-supervision strategy by introducing a predetection head after DSJE. Notably, the predetection head is only active during training to constrain model optimization and does not participate in the inference phase. Consequently, the total loss function of IM-CMDet consists of two components: the detection head loss and the predetection head loss, both of which are computed using the same methodology. The loss functions utilized in this approach are defined as follows:

$$L_{\text{tot}} = \alpha L_{\text{det}} + (1 - \alpha) L_{\text{pre}} \quad (21)$$

$$L_{\text{det}} = L_{\text{reg}} + L_{\text{cls}} \quad (22)$$

$$L_{\text{pre}} = L_{\text{preg}} + L_{\text{pcls}} \quad (23)$$

where  $L_{\text{det}}$  is the detection head loss,  $L_{\text{pre}}$  is the PreHead loss, and  $\alpha$  represents the weight coefficient.  $L_{\text{reg}}/L_{\text{preg}}$  denote the bounding box regression loss in detection head and PreHead, respectively, and  $L_{\text{cls}}/L_{\text{pcls}}$  denote the classification loss in detection head and PreHead, respectively.

The regression task is supervised by generalized intersection over union (GIoU) loss [54], and the classification task is supervised by focal loss [55]. The calculation methods for  $L_{\text{preg}}$  and  $L_{\text{pcls}}$  are as follows:

$$L_{\text{preg}} = \text{GIoU}(\text{box}_t, \text{box}^*) + \text{GIoU}(\text{box}_v, \text{box}^*) \quad (24)$$

$$L_{\text{pcls}} = \text{FL}(\text{cls}_t, \text{cls}^*) + \text{FL}(\text{cls}_v, \text{cls}^*) \quad (25)$$

where  $\text{GIoU}(\cdot)$  and  $\text{FL}(\cdot)$  represent the GIoU loss and focal loss, respectively.  $\text{box}$  and  $\text{cls}$  correspond to the regression and classification predictions, respectively. Subscripts  $t$  and  $v$  indicate the thermal branch and visible branch, respectively, while the superscript  $*$  denotes the object.

## III. EXPERIMENT AND ANALYSIS

### A. Datasets

The primary experiment in this study was conducted using the RGBTDronePerson [38] dataset. To further evaluate the generalization of the proposed method, we conducted additional tests on the VTUAV-det [38] and RTDOD [56] datasets.

1) *RGBTDronePerson Dataset*: The primary experiment in this study was conducted using the RGBTDronePerson [38] dataset, which comprises 6125 pairs of RGB and thermal images captured in a dual camera-equipped drone, DJI Mavic Enterprise Advanced, and annotated with a total of 70 880 object instances. The dataset comprehensively considers two primary factors: illumination and temperature. It encompasses both daytime and nighttime scenes, spanning a wide range of temperature conditions from summer to winter. The majority of images are captured at altitudes between 50 and 80 m, with pitch angles ranging from  $45^\circ$  to  $60^\circ$ , while a limited subset is obtained from vertical perspectives. For the purpose of experimentation, the RGBTDronePerson dataset has been partitioned into 4900 images for training and 1225 images for testing. Following TinyPerson [57], we use average precision (AP) as the performance metric, with intersection over union (IoU) thresholds of 0.25 and 0.50 defining true positive (TP) predictions.

2) *VTUAV-det Dataset*: The VTUAV-det dataset, reannotated by Zhang et al. [38], is derived from the extensive visible and infrared tracking benchmark VTUAV [58], covering a wide range of scenarios and weather conditions. The VTUAV dataset is captured by the DJI Matrice 300 RTK UAV with Zenmuse H20T camera. The thermal camera captures wavelengths in the 8–14  $\mu\text{m}$  range. The flight height is controlled from 5 to 20 m. After recollection, the VTUAV-det dataset comprises 16770 pairs of RGB and thermal images, with 11 392 pairs designated for training and 5378 pairs reserved for testing. These images contain annotations for 124 869 human instances, exhibiting significant size variations. Due

TABLE I  
PERFORMANCE COMPARISONS ON THE RGBTDRONEPERSON DATASET. THE BEST AND SECOND-BEST PERFORMANCES ARE BOLD AND UNDERLINED, RESPECTIVELY

| Method         | mAP <sup>50</sup> <sub>all</sub> | mAP <sub>tiny50</sub> | mAP <sup>50</sup> <sub>tiny1</sub> | mAP <sup>50</sup> <sub>tiny2</sub> | mAP <sup>50</sup> <sub>tiny3</sub> | mAP <sup>50</sup> <sub>small</sub> | mAP <sup>25</sup> <sub>all</sub> | FPS         |
|----------------|----------------------------------|-----------------------|------------------------------------|------------------------------------|------------------------------------|------------------------------------|----------------------------------|-------------|
| Faster-rcnn    | 29.52                            | 29.78                 | 0.0                                | 23.90                              | 36.82                              | <b>37.73</b>                       | 39.83                            | 29.9        |
| Retinanet      | 26.35                            | 27.39                 | 15.63                              | 18.62                              | 38.65                              | 18.74                              | 42.97                            | <b>33.2</b> |
| Cascade-rcnn   | 32.04                            | 32.65                 | 11.55                              | 29.75                              | 38.83                              | <u>33.18</u>                       | 43.53                            | 24.7        |
| ATSS           | 36.45                            | 37.50                 | 17.39                              | 24.85                              | 43.16                              | 28.15                              | 51.28                            | 31.0        |
| ATSS_QLS       | 38.91                            | 40.31                 | 18.30                              | 27.20                              | 45.83                              | 27.04                              | 55.45                            | 30.2        |
| FCOS           | 29.72                            | 30.67                 | 15.45                              | 24.54                              | 33.89                              | 27.52                              | 44.46                            | <u>31.3</u> |
| HRFuser        | 28.11                            | 28.67                 | 2.24                               | 31.28                              | 33.63                              | 26.40                              | 38.43                            | 11.4        |
| TINet          | 26.03                            | 26.38                 | 0.0                                | 20.20                              | 32.43                              | 29.72                              | 36.95                            | 24.4        |
| CDC-Yolofusion | 39.41                            | 40.78                 | 17.51                              | 30.20                              | 46.12                              | 26.99                              | 55.81                            | 22.6        |
| QFDet          | <u>42.20</u>                     | <u>44.30</u>          | <b>20.84</b>                       | 30.90                              | <u>50.55</u>                       | 26.23                              | 57.65                            | 21.4        |
| C2Former       | 41.85                            | 43.41                 | 16.10                              | <u>31.76</u>                       | 49.05                              | 28.02                              | <u>58.01</u>                     | 19.8        |
| DPAL           | 39.35                            | 40.82                 | 18.17                              | 29.25                              | 46.91                              | 25.20                              | 55.61                            | 9.7         |
| IM-CMDet(Ours) | <b>43.61</b>                     | <b>45.18</b>          | <u>18.92</u>                       | <b>32.09</b>                       | <b>51.37</b>                       | 28.61                              | <b>58.81</b>                     | 19.2        |

to the differences in collection conditions compared to the RGBTDronePerson dataset, the object sizes in VTUAV-det are relatively larger. Therefore, we adopt the mean AP (mAP) metric, as used in COCO [59], for evaluation. According to the COCO evaluation protocol, object sizes are categorized as “small,” “medium,” and “large.” Specifically, the VTUAV-det training set includes 7651 small objects, 50 794 medium objects, and 17 869 large objects, while the testing set contains 9864 small objects, 32 731 medium objects, and 5960 large objects.

3) *RTDOD Dataset*: RTDOD [56] is a comprehensive large-scale dataset for visible RGB and thermal object detection, acquired using the DJI Matrice 300 RTK UAV with Zenmuse H20T camera. The dataset covers various scenarios such as suburbs, highways, bridges, as well as different weather conditions including sunny, rainy, and foggy, and a range of lighting conditions including day and night. It encompasses ten categories, including people, vehicles, trucks, and motorcycles. To address the significant category imbalance that could potentially compromise model performance, we refined the original RTDOD dataset by retaining only four categories: “Person,” “Truck,” “Motorcycle,” and “Car.” These categories collectively account for 94.71% of all instances. The refined dataset comprises 9578 pairs of training images and 3328 pairs of test images, totaling 169 446 instances. Importantly, the original train-test split was preserved after this filtering process. For both the VTUAV-det and RTDOD datasets, we adhere to the COCO [59] evaluation criteria.

### B. Training and Testing Details

We implemented this model using PyTorch [60] and the MMDetectionV2 framework [61]. All image inputs were resized to  $640 \times 512$  while maintaining their aspect ratio. The network backbone is ResNet50 [62], which was pretrained on ImageNet [63]. The model was trained for 12 epochs using the stochastic gradient descent (SGD) optimizer with a momentum of 0.9, a learning rate of 0.01, a weight decay factor of 0.0001, and a batch size of 8. To prevent overfitting, we selected the epoch with the best validation performance as the final model. For data augmentation, we employed random flipping. During testing, the non-maximum suppression (NMS) IoU threshold

for RGBTDronePerson was set to 0.35, while for VTUAV-det and RTDOD, it was set to 0.65. The confidence threshold was set to 0.05. All experiments were conducted on a single NVIDIA GeForce RTX 3090 GPU with 24 GB of memory.

### C. Comparison With State-of-the-Art Methods

In this section, we conduct a comprehensive comparison of IM-CMDet against several state-of-the-art object detection algorithms. These algorithms are categorized based on their approaches to small object detection and multimodal sensor fusion. For small object detection, we focus on two prominent methods: QFDet [38] and the adaptive training sample selection\_quality-aware learning strategy (ATSS\_QLS) detector [38], an enhanced variant of the ATSS detector [64]. Both methods have demonstrated significant improvements in performance, particularly for small objects, with the latter serving as a key baseline for our proposed method. For multimodal object detection, we compare IM-CMDet with leading sensor-fusion algorithms such as TINet [31], HRFuser [65], C2Former [42], CDC-YoloFusion [51], and DPAL [66]. Additionally, we evaluate baseline detectors for RGBT object detection, including Faster R-CNN [67], Cascade R-CNN [68], RetinaNet [55], FCOS [69], and ATSS [64]. These methods employ a two-stream architecture to extract features from visible and thermal modalities separately, followed by feature fusion through a  $1 \times 1$  convolutional layer.

1) *Results on RGBTDronePerson*: We compared our method with the comparison methods on the RGBTDronePerson dataset in the same settings. The results are shown in Table I. “tiny1,” “tiny2,” “tiny3,” and “small” denote absolute object sizes that are in the range of [0, 8), [9, 12), [12, 20), and [20, 32], respectively. From an overall performance perspective, IM-CMDet achieves an mAP<sup>all</sup><sub>50</sub> of 43.61% and an mAP<sup>tiny</sup><sub>50</sub> of 45.18%; on this dataset, we achieved optimal levels. In particular, IM-CMDet surpasses the baseline network by 4.7% and surpasses QFDet by 1.41%, which may be attributed to our object feature enhancement and interaction strategy for small objects. However, from the perspective of the tiny1 metric, QFDet outperforms our method, likely due to its quality-aware strategy based on point quality in the network.

TABLE II  
PERFORMANCE COMPARISONS ON THE VTUAV-DET DATASET. THE BEST AND SECOND-BEST PERFORMANCES ARE BOLDED AND UNDERLINED, RESPECTIVELY

| Method                | mAP          | mAP <sub>50</sub> | mAP <sub>75</sub> | mAP <sub>s</sub> | mAP <sub>m</sub> | mAP <sub>l</sub> | FPS         |
|-----------------------|--------------|-------------------|-------------------|------------------|------------------|------------------|-------------|
| Faster-rcnn           | 26.50        | 58.30             | 20.50             | 1.20             | 28.50            | 54.50            | 30.6        |
| Retinanet             | 22.20        | 52.20             | 16.00             | 2.70             | 22.10            | 55.90            | <b>33.0</b> |
| Cascade-rcnn          | 28.40        | 62.20             | 21.90             | 3.0              | <u>30.40</u>     | 56.60            | 26.1        |
| ATSS                  | 28.50        | 66.00             | 20.30             | 8.4              | 28.20            | 55.60            | 31.3        |
| ATSS_QLS              | <u>30.70</u> | 69.60             | <u>22.60</u>      | <u>12.40</u>     | 30.20            | <u>56.90</u>     | 30.4        |
| FCOS                  | 27.40        | 65.10             | 19.10             | 7.5              | 27.50            | 53.00            | <u>32.0</u> |
| HRFuser               | 28.50        | 61.80             | 22.10             | 4.40             | 30.40            | 55.20            | 11.5        |
| TINet                 | 26.70        | 60.20             | 19.70             | 1.90             | 29.30            | 51.50            | 26.4        |
| CDC-YoloFusion        | 30.10        | 69.30             | 21.60             | 11.50            | 29.30            | 55.70            | 23.0        |
| QFDet                 | 30.60        | <u>70.20</u>      | 22.00             | 12.20            | 30.10            | <u>56.90</u>     | 22.7        |
| C2Former              | 29.80        | 68.70             | 21.60             | 11.00            | 29.50            | 55.90            | 20.0        |
| DPAL                  | 29.60        | 68.40             | 21.50             | 11.00            | 29.10            | 56.20            | 9.7         |
| <b>IM-CMDet(Ours)</b> | <b>31.50</b> | <b>70.70</b>      | <b>23.00</b>      | <b>12.80</b>     | <b>30.70</b>     | <b>57.80</b>     | 19.3        |

![Figure 5: Visualization of the selected methods on RGBTDronePerson. The figure shows a 4x6 grid of images. The first column displays the original visible modality images. The subsequent five columns show the object detection results from different methods: 'Ours', 'ATSS', 'ATSS_QLS', 'QFDet', and 'Tinet'. Each method's results are visualized with colored bounding boxes around detected objects. The scenes include urban areas, roads, and night scenes with various lighting conditions.](a86610f7a0e579fec9f34dea52fa088b_img.jpg)

Figure 5: Visualization of the selected methods on RGBTDronePerson. The figure shows a 4x6 grid of images. The first column displays the original visible modality images. The subsequent five columns show the object detection results from different methods: 'Ours', 'ATSS', 'ATSS\_QLS', 'QFDet', and 'Tinet'. Each method's results are visualized with colored bounding boxes around detected objects. The scenes include urban areas, roads, and night scenes with various lighting conditions.

Fig. 5. Visualization of the selected methods on RGBTDronePerson.

Although our method performs well overall, its performance is lower compared to other methods on the small scale. It may be because objects at this scale only account for 2% of the dataset, which selectively diminishes learning for objects at this scale. C2Former [42] demonstrates strong performance on Tiny2 and mAP<sup>25</sup><sub>all</sub> metrics, as previously shown in Table I. Nevertheless, these gains are accompanied by a substantial computational burden due to the extensive use of attention mechanisms, which limits its applicability in resource-constrained scenarios.

The qualitative comparisons among IM-CMDet, QFDet, ATSS, ATSS\_QLS, and TINet are shown in Fig. 5. In the figure, the first column presents the original images from the visible modality, while the remaining columns display object detection results produced by various methods. The experimental results across various scenes demonstrate that,

compared with the baseline approaches, the proposed method achieves a higher TP rate while maintaining a lower false positive (FP) rate. Specifically, in Scene 1, where the number of objects is relatively high, the proposed method achieves a more comprehensive detection performance. In Scene 3, the superior detection capability of the proposed method, particularly in cases where objects are visually similar to the background, can likely be attributed to the DSJE module, which enhances the features of small objects. Furthermore, with the assistance of the CSOFS module, specifically designed for small object detection, the network effectively integrates information from both modalities and improves its sensitivity to small objects. This results in significantly enhanced performance in Scenes 2 and 4. However, in Scenario 4, the model is unable to reliably detect targets situated in low-light conditions and heavily

![Figure 6: Visualization of selected methods on VTUAV-det. The figure shows a grid of images comparing the performance of six methods: Visible, Ours, ATSS, ATSS_QLS, QFDet, and Tinet. Each row represents a different scene with varying lighting conditions. The 'Ours' method consistently shows more accurate object detection with better localization and fewer false positives compared to the other methods.](349ca0a6a9c2e2651a4deeeaf8be6da1_img.jpg)

Figure 6: Visualization of selected methods on VTUAV-det. The figure shows a grid of images comparing the performance of six methods: Visible, Ours, ATSS, ATSS\_QLS, QFDet, and Tinet. Each row represents a different scene with varying lighting conditions. The 'Ours' method consistently shows more accurate object detection with better localization and fewer false positives compared to the other methods.

Fig. 6. Visualization of selected methods on VTUAV-det.

occluded by trees, where limited illumination and severe occlusion substantially weaken the visibility of discriminative features, leading to missed or uncertain detections.

In summary, the proposed method can more effectively utilize information from both RGB and thermal images, thereby better addressing the significant performance degradation caused by severe illumination variations in RGB images. Moreover, the examination of the third and fourth columns suggests that the modified ATSS\_QLS algorithm achieves overall performance improvements over the original ATSS algorithm. Specifically, the ATSS\_QLS algorithm demonstrates a higher TP rate, accompanied by fewer false and missed detections. These results indicate that the quality-aware learning strategy (QLS) assignment strategy effectively contributes to improved detection performance for small objects.

2) *Results on VTUAV-det*: On this dataset, the objects exhibit greater size variation, and we use the COCO standard to measure the performance of the comparison methods. The quantitative experimental results are shown in Table II. Compared to the ATSS\_QLS method, our approach improves by 0.9% in mAP and mAP<sub>50</sub> is 0.5% higher than the second-best method QFDet. In the mAP<sub>s</sub> metric, our method is 0.6% higher than QFDet and 0.4% higher than ATSS\_QLS, while in the mAP<sub>l</sub> metric, it is 0.9% higher than QFDet. This indicates that our method also performs well under conditions of significant size variation, which may be attributed to the effectiveness of our detail-semantic joint enhancement module aimed at enhancing intramodal objects.

The subjective comparison results are shown in Fig. 6. Four scenes with varying lighting conditions were selected for testing to comprehensively evaluate the performance of the proposed method. Compared to other methods, our approach achieves a higher number of TP and fewer FP. Specifically, in Scene 1, where objects are unevenly distributed and clustered, the proposed detail enhancement strategy helps the network distinguish between objects, enabling more accurate localization. However, some missed detections still occur, which may be due to the model placing relatively more emphasis on the infrared modality, causing targets that do not exhibit distinctive features in the infrared image to be overlooked. In

Scene 2, where small objects are densely distributed and the distinction between objects and the background is minimal, leading to poor object identifiability in the RGB modality, the combination of the detail enhancement method and the small-object feature interaction strategy further improves the network's sensitivity to objects, reducing missed and false detections. In Scenes 3 and 4, where lighting conditions are poor, the proposed modality interaction strategy allows our method to more effectively distinguish between similar objects in thermal images (e.g., in Scene 3, where a bright spot in the thermal image near a street-side shop is mistakenly identified as an object by comparative methods), achieving higher detection accuracy with fewer FP.

3) *Results on RTDOD*: Based on Table III, we compare the performance of various methods on the RTDOD dataset, emphasizing their detection capabilities across different object sizes. Our proposed method achieves the highest overall performance, with an mAP of 52.40%, an mAP<sub>50</sub> of 81.40%, and an mAP<sub>75</sub> of 58.60%. This improvement is primarily attributed to a substantial gain in small object detection (mAP<sub>s</sub>: 37.10%), where our method significantly outperforms all other approaches. For medium- and large-scale objects, Cascade R-CNN exhibits strong performance, achieving the highest mAP<sub>m</sub> (60.90%) and mAP<sub>l</sub> (72.50%). Meanwhile, HRFuser, a cross-modal joint detection method, also shows competitive results, particularly in medium-sized object detection (mAP<sub>m</sub>: 59.50%). However, both methods struggle with small object detection, which significantly limits their overall performance. These results highlight the advantage of our method in addressing the challenges of small object detection while maintaining competitive performance on other object scales.

Fig. 7 presents a qualitative comparison of different methods on the RTDOD dataset, highlighting the superior performance of our approach across diverse scenarios. In small-object detection tasks, particularly evident in the first row, our method accurately identifies distant and challenging objects that are often missed or incompletely detected by other methods such as ATSS and QFDet. Nevertheless, the proposed method fails to accurately detect a few small targets that

TABLE III  
PERFORMANCE COMPARISONS ON THE RTDOD DATASET. THE BEST AND SECOND-BEST PERFORMANCES ARE BOLDED AND UNDERLINED, RESPECTIVELY

| Method                | mAP          | mAP <sub>50</sub> | mAP <sub>75</sub> | mAP <sub>s</sub> | mAP <sub>m</sub> | mAP <sub>l</sub> | FPS         |
|-----------------------|--------------|-------------------|-------------------|------------------|------------------|------------------|-------------|
| Faster-rcnn           | 47.70        | 72.40             | 54.40             | 24.10            | 59.20            | 71.70            | 31.4        |
| Retinanet             | 39.40        | 68.10             | 40.20             | 15.10            | 48.00            | 71.10            | <b>34.5</b> |
| Cascade-rcnn          | 49.80        | 73.80             | <u>56.60</u>      | 27.30            | <b>60.90</b>     | <u>72.50</u>     | 26.8        |
| ATSS                  | 49.10        | 78.80             | 54.00             | 32.60            | 56.70            | 70.40            | 32.2        |
| ATSS_QLS              | <u>49.60</u> | 79.80             | 54.60             | 33.40            | 56.80            | 70.40            | 31.6        |
| FCOS                  | 45.90        | 77.20             | 48.50             | 27.90            | 53.10            | 70.10            | <u>32.7</u> |
| HRFuser               | <u>49.60</u> | 72.80             | 56.20             | 31.00            | <u>59.50</u>     | 66.80            | 11.4        |
| TINet                 | 46.80        | 71.60             | 53.50             | 23.40            | 58.40            | 70.70            | 26.3        |
| CDC-YoloFusion        | 49.00        | 79.10             | 53.70             | <u>34.30</u>     | 56.20            | 68.40            | 23.1        |
| QFDet                 | 49.20        | <u>81.10</u>      | 53.10             | 33.60            | 56.00            | 69.10            | 22.5        |
| C2Former              | 48.60        | 79.20             | 52.80             | 34.00            | 55.30            | 67.70            | 20.6        |
| DPAL                  | 47.60        | 78.70             | 51.60             | 31.70            | 54.90            | 66.90            | 9.9         |
| <b>IM-CMDet(Ours)</b> | <b>52.40</b> | <b>81.40</b>      | <b>58.60</b>      | <b>37.10</b>     | 59.10            | <b>72.70</b>     | 19.5        |

![Figure 7: Visualization of selected methods on RTDOD. The figure shows a 4x6 grid of images. The first column shows the original Thermal images. The subsequent columns show the detection results from 'Ours', 'ATSS', 'ATSS_QLS', 'QFDet', and 'Tinet' respectively. The images depict various road scenes with vehicles, including cars, trucks, and motorcycles, under different lighting and weather conditions. The 'Ours' method consistently shows more accurate and precise bounding boxes compared to the other methods, especially in challenging conditions like fog or low light.](d29cfbf30a471dc06a78be27f86bd1cf_img.jpg)

Figure 7: Visualization of selected methods on RTDOD. The figure shows a 4x6 grid of images. The first column shows the original Thermal images. The subsequent columns show the detection results from 'Ours', 'ATSS', 'ATSS\_QLS', 'QFDet', and 'Tinet' respectively. The images depict various road scenes with vehicles, including cars, trucks, and motorcycles, under different lighting and weather conditions. The 'Ours' method consistently shows more accurate and precise bounding boxes compared to the other methods, especially in challenging conditions like fog or low light.

Fig. 7. Visualization of selected methods on RTDOD.

extremely low observability in both visible and infrared modalities within this scenario, which suggests that its scene interpretation capability could be further improved. In dense-object scenarios, as shown in the second row, our approach demonstrates precise localization and reduced false negatives, effectively balancing precision and recall in crowded scenes. Under foggy conditions depicted in the third row, our method exhibits remarkable robustness by accurately detecting objects obscured by reduced visibility, outperforming other methods like TINet. In the fourth row, the effectiveness of our method is further demonstrated by leveraging complementary features from both thermal and visible images, where the information from thermal images effectively filters out distracting features in the visible images, resulting in precise and reliable detection. These results underscore the advantages of our approach in cross-modal small-object detection tasks.

4) *Efficiency Comparison:* The backbones, parameter counts, and computational costs of the compared methods in this article are summarized in Table IV. To ensure a fair comparison, all comparison methods employ ResNet50 [62] as the backbone network. The only exception is HRFuser [65], where we keep the original backbone architecture in our experiments

TABLE IV  
COMPARISON OF NETWORK BACKBONES, PARAMETER COUNTS, AND COMPUTATIONAL COSTS FOR THE METHODS IN OUR EXPERIMENTS

| Method                | Backbone | Param.(MB)   | GFLOPs       |
|-----------------------|----------|--------------|--------------|
| Faster-rcnn           | ResNet50 | 97.17        | 111.77       |
| Retinanet             | ResNet50 | 59.82        | 98.97        |
| Cascade-rcnn          | ResNet50 | 92.61        | 113.8        |
| ATSS                  | ResNet50 | <u>59.48</u> | 97.45        |
| ATSS_QLS              | ResNet50 | <u>59.48</u> | 97.45        |
| FCOS                  | ResNet50 | 78.57        | <u>94.41</u> |
| HRFuser               | HRFormer | <b>48.79</b> | <b>52.92</b> |
| TINet                 | ResNet50 | 88.78        | 108.23       |
| CDC-Yolofusion        | ResNet50 | 83.54        | 98.09        |
| QFDet                 | ResNet50 | 60.18        | 162.86       |
| C2Former              | ResNet50 | 118.69       | 145.54       |
| DPAL                  | ResNet50 | 114.86       | 144.63       |
| <b>IM-CMDet(Ours)</b> | ResNet50 | 105.04       | 133.93       |

since its primary innovations lie in the backbone design itself. From Table IV, it can be observed that most recently proposed methods introduce a noticeable increase in computational cost

TABLE V  
OVERALL ABLATION EXPERIMENTS. THE BEST PERFORMANCES ARE BOLDED

| Method      | DSJE | CSOFS | PreHead | mAP <sup>50</sup> <sub>all</sub> | Param.(MB)   | GFlops       | FPS         |
|-------------|------|-------|---------|----------------------------------|--------------|--------------|-------------|
| Baseline    |      |       |         | 38.91                            | <b>59.48</b> | <b>97.45</b> | <b>30.2</b> |
| M1          | ✓    |       |         | 40.33                            | 76.36        | 102.75       | 25.3        |
| M2          |      | ✓     |         | 40.22                            | 88.12        | 125.81       | 21.5        |
| M3          |      |       | ✓       | 41.27                            | 59.48        | 97.45        | 29.9        |
| M4          | ✓    | ✓     |         | 42.63                            | 105.04       | 133.93       | 19.1        |
| M5          | ✓    |       | ✓       | 41.90                            | 76.36        | 102.75       | 24.7        |
| M6          |      | ✓     | ✓       | 41.74                            | 88.12        | 125.81       | 21.4        |
| <b>Ours</b> | ✓    | ✓     | ✓       | <b>43.61</b>                     | 105.04       | 133.93       | 19.2        |

TABLE VI  
MODULEWISE PARAMETERS AND FLOPs

| Module     | DSJE | DFWG  | FRN   |
|------------|------|-------|-------|
| Param.(MB) | 12.3 | 17.7  | 10.9  |
| Gflops     | 7.85 | 11.34 | 18.95 |

compared with the baseline. Although QFDet employs fewer parameters, it suffers from higher inference overhead due to the use of a computationally intensive predetection head during testing. In contrast, our method restricts this component to the training phase as supervision, thereby reducing inference complexity. Overall, while the additional modules in our approach lead to a moderate increase in parameter count, the model preserves competitive inference speed and incurs only a modest rise in GFlops, striking a favorable balance between efficiency and performance. A more detailed analysis of parameter size and computational cost for each component of the proposed framework is provided in Section III-D.

### D. Ablation Study

1) *Overall Ablation*: Ablation studies were conducted on the RGBTDronePerson dataset to systematically evaluate the effectiveness of the proposed components. The results in Table V demonstrate that the proposed modules, fusion strategies, and training schemes are indeed beneficial. Specifically, the proposed method exhibited a 4.7% improvement in performance compared with the baseline. The incorporation of the DSJE module contributed a 1.42% performance enhancement to the network. The introduction of the fusion strategy yielded a 1.31% performance gain. Moreover, the three modules exhibit interdependent relationships and achieve collective enhancement—when operating individually, their effectiveness was somewhat constrained. Specifically, integrating DSJE modules with CSOFS methods resulted in further performance improvements, attributed to the synergistic combination of enhanced discriminative information and effective cross-modal fusion. By incorporating the dual-supervision scheme, the network achieves additional gains, highlighting the importance of enhancing feature extraction to improve fusion effectiveness. Notably, since the dual supervision is applied only during training, it introduces no additional parameters or computational cost during inference. Furthermore, its effects become more pronounced when jointly employed with the

TABLE VII  
ABLATION ON DSJE MODULE. THE BEST PERFORMANCES ARE BOLDED

| Method      | Detail Info | Enhancement Refe | mAP <sup>50</sup> <sub>all</sub> |
|-------------|-------------|------------------|----------------------------------|
| M6          |             |                  | 41.74                            |
| M7          | ✓           |                  | 40.09                            |
| M8          |             | ✓                | 43.26                            |
| <b>Ours</b> | ✓           | ✓                | <b>43.61</b>                     |

DSJE modules, where the enhanced supervision strategy further boosts the operational effectiveness of DSJE. Beyond performance evaluation, we also analyze model complexity in terms of parameter count, floating-point operations (FLOPs) and inference speed, as shown in Table V. Although the proposed method introduces a certain computational overhead, the performance gains—especially for small object detection—demonstrate a favorable tradeoff. To better illustrate the efficiency of each component, we provide a detailed breakdown of the parameter count and FLOPs for each module, as shown in Table VI. In particular, the DFWG module processes deep semantic features with high channel dimensions extracted from the backbone, resulting in a noticeable increase in parameter count while the associated growth in computational complexity remains relatively modest as the low spatial resolutions.

2) *Ablation on DSJE*: This study further examines the impact of the detail enhancement and ER components on overall performance in the DSJE module, as illustrated in Table VII. Compared with the M6 model, the integration of ER improves model performance by 1.52%, demonstrating that the hierarchical interaction strategy proposed in our method effectively optimizes multilevel feature representations. The elimination of detail enhancement from the original image processing pipeline results in a 0.35% performance decline, confirming that the proposed detail enhancement mechanism significantly enhances discriminative information of objects compared to the baseline network. However, removing the enhanced baseline module leads to a more severe degradation (1.65% performance drop) relative to the M6 model. One plausible explanation lies in that the isolated use of detail enhancement (without ER) introduces substantial noise from shallow high-frequency details extracted by the Laplacian filter. Specifically, shallow edge features often contain irrelevant structural information (e.g., vegetation or architectural

TABLE VIII  
ABLATION ON CSOFS MODULE. THE BEST  
PERFORMANCES ARE BOLDED

| Method | DFWG | FRN | mAP <sup>50</sup> <sub>all</sub> |
|--------|------|-----|----------------------------------|
| M5     |      |     | 41.90                            |
| M9     | ✓    |     | 42.25                            |
| M10    |      | ✓   | 42.18                            |
| Ours   | ✓    | ✓   | <b>43.61</b>                     |

edges) that can misguide network attention mechanisms. The joint implementation of ER and detail enhancement strategically amplifies object-specific features while suppressing background interference.

3) *Ablation on CSOFS:* In this study, we conducted systematic ablation experiments to evaluate the components of our proposed CSOFS, specifically designed for small-object detection. Comparative results against the M5 model reveal that both the DFWG and FRN modules contribute measurably to performance enhancement as summarized in Table VIII. While compared with the completed method, the removal of DFWG induces a marked performance deterioration (1.43% reduction), likely attributable to compromised redundancy filtering capacity and diminished sensitivity to small objects. Similarly, excluding FRN results in a 1.36% performance decline, potentially due to inadequate learning of cross-modal feature relevance compared to the complete configuration. This degradation suggests FRN’s critical role in establishing intermodal semantic alignment, particularly for distinguishing subtle object characteristics from complex backgrounds (e.g., Scenarios 2 and 3 in Fig. 6).

To further validate the performance of the CSOFS strategy, we conducted comprehensive robustness tests by introducing artificially induced modal biases, as illustrated in Fig. 8. Specifically, two distinct perturbation strategies were employed: pixelwise translation and degree-by-degree center rotation, which were applied to both our method and the ablation variants. As demonstrated in Fig. 8(a), although the performance of all methods degrades under artificially introduced perturbations, our approach consistently maintains superior performance. The performance degradation analysis in Fig. 8(b) reveals that the incorporation of either FRN or DFWG significantly mitigated performance deterioration under different perturbation intensities when compared to the M5 method.

4) *Visualization of Intermediate Feature:* To further intuitively understand the roles of DSJE and FRN in our framework, we visualize the intermediate features, as shown in Fig. 9. From top to bottom, each column represents the original image, and the C3–C5 feature layers, respectively. It can be clearly observed that the features directly extracted by the backbone exhibit weak responses around small objects. After processing with the DSJE module, the object responses in both visible and infrared modalities are significantly enhanced, indicating that the hierarchical interaction and shallow detail injection strategies effectively improve feature detail preservation and enhance the representation capability across multiple scales. However, despite the

![Figure 8: Robustness analysis of four models under increasing perturbation intensity. (a) Performance under varying perturbations. (b) Relative degradation under varying perturbations.](303b94716b6713757d1fdf940a6b345f_img.jpg)

Figure 8 consists of two line graphs. Graph (a) is titled 'Performance under Perturbation' and plots 'Performance' (y-axis, 34 to 44) against 'Angle (deg) / Shift (pixel)' (x-axis, 0 to 12). It shows performance for four models (M9, M10, M5, Ours) under two perturbation types: Angle (solid lines) and Shift (dashed lines). Ours (red lines) maintains the highest performance across all perturbations. Graph (b) is titled 'Relative Performance degradation (compared to 0° / 0 shift)' and plots 'Relative degradation (means better)' (y-axis, 0.00 to 0.20) against the same x-axis. It shows the relative degradation for the same models and perturbation types. Ours (red lines) shows the lowest relative degradation, indicating better robustness.

Figure 8: Robustness analysis of four models under increasing perturbation intensity. (a) Performance under varying perturbations. (b) Relative degradation under varying perturbations.

Fig. 8. Robustness analysis of four models under increasing perturbation intensity. (a) Performance under varying perturbations. (b) Relative degradation under varying perturbations.

improvements introduced by the DSJE module, inconsistencies in feature responses across modalities persist, and the visible modality still suffers from weakened representations under low illumination. A comparison between Fig. 9(d) and (e) reveals that the FRN module effectively compensates for the weak visible features by aligning them with infrared information. In addition, the response misalignment observed in Fig. 9(d) is noticeably alleviated after the application of the FRN module.

5) *Sensitivity Analysis:* The weighting configuration of loss functions critically governs network training preference. To identify the optimal weighting configuration for our dual supervision strategy, we conducted a systematic parameter sweep through progressive weight allocation. Specifically, we incremented the  $\alpha$  coefficient from 0.1 to 0.9 in 0.1 intervals while maintaining a complementary  $\beta$  value ( $\beta = 1 - \alpha$ ) to preserve weight summation unity. Our methodical evaluation reveals a distinct performance maximum at  $\alpha = \beta = 0.5$ , as quantitatively demonstrated in Fig. 10. This balanced configuration achieves an excellent balance between intramodal feature extraction and final detection results. Notably, performance degradation observed at extreme weight ratios ( $\alpha < 0.3$  or  $\alpha > 0.7$ ) underscores the necessity of balanced supervision—excessive emphasis on either component disrupts the delicate equilibrium required for effective small-object detection in complex environments.

![Figure 9: Visualization of intermediate feature maps. The figure is a 4x5 grid of images. The first row shows original RGB and infrared images. The subsequent rows show heatmaps representing feature maps at different stages: (a) and (b) show features from the backbone; (c) and (d) show features after the DSJE module; (e) shows features after the FRN module. Green bounding boxes highlight specific regions of interest across all feature maps.](7832324609ad3cc688064e0341612b32_img.jpg)

Figure 9: Visualization of intermediate feature maps. The figure is a 4x5 grid of images. The first row shows original RGB and infrared images. The subsequent rows show heatmaps representing feature maps at different stages: (a) and (b) show features from the backbone; (c) and (d) show features after the DSJE module; (e) shows features after the FRN module. Green bounding boxes highlight specific regions of interest across all feature maps.

Fig. 9. Visualization of intermediate feature maps. (a) and (b) Infrared and visible features extracted by the backbone, respectively. (c) and (d) Corresponding features refined after DSJE module. (e) Visible features further processed through the FRN module.

![Figure 10: Performance under different alpha values. A line graph showing Performance (Y-axis, 20 to 60) versus Alpha (X-axis, 0.1 to 0.9). Three lines represent mAP50 (orange), mAP Tiny (blue), and mAP25 (green). mAP25 shows the highest performance, followed by mAP Tiny, and then mAP50. All lines show a slight peak around Alpha = 0.6.](411fa16c3211377525ba37c57784fee0_img.jpg)

| Alpha | mAP50 | mAP Tiny | mAP25 |
|-------|-------|----------|-------|
| 0.1   | 39    | 40       | 55    |
| 0.2   | 40    | 41       | 56    |
| 0.3   | 41    | 42       | 57    |
| 0.4   | 41    | 42       | 56    |
| 0.5   | 44    | 45       | 58    |
| 0.6   | 43    | 44       | 59    |
| 0.7   | 40    | 41       | 57    |
| 0.8   | 41    | 42       | 58    |
| 0.9   | 42    | 42       | 56    |

Figure 10: Performance under different alpha values. A line graph showing Performance (Y-axis, 20 to 60) versus Alpha (X-axis, 0.1 to 0.9). Three lines represent mAP50 (orange), mAP Tiny (blue), and mAP25 (green). mAP25 shows the highest performance, followed by mAP Tiny, and then mAP50. All lines show a slight peak around Alpha = 0.6.

Fig. 10. Performance under different alpha values.

## IV. CONCLUSION

In this article, we introduce a small object detection method based on the fusion of UAV aerial RGBT images, termed IM-CMDet. By integrating intramodel discriminative feature enhancement with a cross-modal feature alignment network specifically designed for small object characteristics, our method effectively enhances the performance of detecting small objects under varying illumination. Extensive experiments on three datasets demonstrate that our approach achieves superior performance in scenarios characterized by complex backgrounds.

Despite the significant advancements in accuracy and robustness of cross-modal fusion achieved by our approach, there remains potential for optimization implied in the results of experiments. In terms of inference efficiency, IM-CMDet demonstrates only sub-real-time performance, suggesting that there is still room for improving the efficiency of the model. However, in real-world scenarios, fast detection is crucial for better adaptation to video stream data. Future research could

investigate more efficient attention mechanisms or adaptive window attention methods to enhance real-time detection performance. Moreover, the proposed fusion method may place excessive emphasis on the infrared modality under well-illuminated conditions, thereby attenuating the more discriminative features from the visible spectrum. Future work could incorporate illumination-aware mechanisms to dynamically balance multimodal feature representations, further enhancing overall detection performance.

## REFERENCES

- [1] P. Yan, Y. Feng, Q. Han, H. Wu, Z. Hu, and S. Kang, "Revolutionizing crop phenotyping: Enhanced UAV LiDAR flight parameter optimization for wide-narrow row cultivation," *Remote Sens. Environ.*, vol. 320, Apr. 2025, Art. no. 114638.
- [2] M. Kucharczyk and C. H. Hugenholtz, "Remote sensing of natural hazard-related disasters with small drones: Global trends, biases, and research opportunities," *Remote Sens. Environ.*, vol. 264, Oct. 2021, Art. no. 112577.
- [3] F. Outay, H. A. Mengash, and M. Adnan, "Applications of unmanned aerial vehicle (UAV) in road safety, traffic and highway infrastructure management: Recent advances and challenges," *Transp. Res. A, Policy Pract.*, vol. 141, pp. 116–129, Nov. 2020.
- [4] X. Meng, S. Zhang, Q. Liu, G. Yang, and W. Sun, "Uncertain category-aware fusion network for hyperspectral and LiDAR joint classification," *IEEE Trans. Geosci. Remote Sens.*, vol. 62, 2024, Art. no. 5523015.
- [5] Q. Liu, X. Meng, F. Shao, and S. Li, "Supervised-unsupervised combined deep convolutional neural networks for high-fidelity pansharpening," *Inf. Fusion*, vol. 89, pp. 292–304, Jan. 2023.
- [6] Y. Zhang, C. Wu, W. Guo, T. Zhang, and W. Li, "CFANet: Efficient detection of UAV image based on cross-layer feature aggregation," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, 2023, Art. no. 5608911.
- [7] L. Chen, C. Liu, W. Li, Q. Xu, and H. Deng, "DTSSNet: Dynamic training sample selection network for UAV object detection," *IEEE Trans. Geosci. Remote Sens.*, vol. 62, 2024, Art. no. 5902516.
- [8] J. Xu et al., "YOLOOW: A spatial scale adaptive real-time object detection neural network for open water search and rescue from UAV aerial imagery," *IEEE Trans. Geosci. Remote Sens.*, vol. 62, 2024, Art. no. 5623115.

- [9] M. Zhang, R. Zhang, J. Zhang, J. Guo, Y. Li, and X. Gao, "Dim2Clear network for infrared small target detection," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, 2023, Art. no. 5001714.
- [10] M. Zhang, Y. Wang, J. Guo, Y. Li, X. Gao, and J. Zhang, "IRSAM: Advancing segment anything model for infrared small target detection," 2024, *arXiv:2407.07520*.
- [11] Y. Zhang, M. Ye, G. Zhu, Y. Liu, P. Guo, and J. Yan, "FFCA-YOLO for small object detection in remote sensing images," *IEEE Trans. Geosci. Remote Sens.*, vol. 62, 2024, Art. no. 5611215.
- [12] X. Wu, D. Hong, and J. Chanussot, "UIU-Net: U-Net in U-Net for infrared small object detection," *IEEE Trans. Image Process.*, vol. 32, pp. 364–376, 2023.
- [13] B. Bosquet, D. Cores, L. Seidenari, V. M. Brea, M. Mucientes, and A. D. Bimbo, "A full data augmentation pipeline for small object detection based on generative adversarial networks," *Pattern Recognit.*, vol. 133, Jan. 2023, Art. no. 108998.
- [14] M. Zhang et al., "RKformer: Runge–Kutta transformer with random-connection attention for infrared small target detection," in *Proc. 30th ACM Int. Conf. Multimedia*, Oct. 2022, pp. 1730–1738.
- [15] R. Jing, W. Zhang, Y. Liu, W. Li, Y. Li, and C. Liu, "An effective method for small object detection in low-resolution images," *Eng. Appl. Artif. Intell.*, vol. 127, Jan. 2024, Art. no. 107206.
- [16] S. Ma, Y. Zhang, L. Peng, C. Sun, B. Ding, and Y. Zhu, "OWRT-DETR: A novel real-time transformer network for small-object detection in open-water search and rescue from UAV aerial imagery," *IEEE Trans. Geosci. Remote Sens.*, vol. 63, 2025, Art. no. 4205313.
- [17] M. Zhang, H. Yang, J. Guo, Y. Li, X. Gao, and J. Zhang, "IRPruneDet: Efficient infrared small target detection via wavelet structure-regularized soft channel pruning," in *Proc. AAAI Conf. Artif. Intell.*, vol. 38, 2024, pp. 7224–7232.
- [18] C. Jiang et al., "Object detection from UAV thermal infrared images and videos using YOLO models," *Int. J. Appl. Earth Observ. Geoinf.*, vol. 112, Aug. 2022, Art. no. 102912.
- [19] Z. Zhao, C. Wang, C. Li, Y. Zhang, and J. Tang, "Modality conversion meets superresolution: A collaborative framework for high-resolution thermal UAV image generation," *IEEE Trans. Geosci. Remote Sens.*, vol. 62, 2024, Art. no. 5001314.
- [20] F. Moradi, F. D. Javan, and F. Samadzadegan, "Potential evaluation of visible-thermal UAV image fusion for individual tree detection based on convolutional neural network," *Int. J. Appl. Earth Observ. Geoinf.*, vol. 113, Sep. 2022, Art. no. 103011.
- [21] M. Yuan, Y. Wang, and X. Wei, "Translation, scale and rotation: Cross-modal alignment meets RGB-infrared vehicle detection," in *Proc. Eur. Conf. Comput. Vis.*, 2022, pp. 509–525.
- [22] J. Wang, Y. Zhao, and L. Dou, "Feature correction and semantic guidance for multimodal crowd counting," *Appl. Soft Comput.*, vol. 181, Sep. 2025, Art. no. 113449.
- [23] W. Zhao, S. Xie, F. Zhao, Y. He, and H. Lu, "MetaFusion: Infrared and visible image fusion via meta-feature embedding from object detection," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2023, pp. 13955–13965.
- [24] D. Rao, T. Xu, and X.-J. Wu, "TGFuse: An infrared and visible image fusion approach based on transformer and generative adversarial network," *IEEE Trans. Image Process.*, early access, May 10, 2023, doi: [10.1109/TIP.2023.3273451](https://doi.org/10.1109/TIP.2023.3273451).
- [25] Y.-T. Chen, J. Shi, Z. Ye, C. Mertz, D. Ramanan, and S. Kong, "Multimodal object detection via probabilistic ensembling," in *Proc. ECCV*, Switzerland, 2022, pp. 139–158.
- [26] Y. Sun, B. Cao, P. Zhu, and Q. Hu, "Drone-based RGB-infrared cross-modality vehicle detection via uncertainty-aware learning," *IEEE Trans. Circuits Syst. Video Technol.*, vol. 32, no. 10, pp. 6700–6713, Oct. 2022.
- [27] H. Liang, J. Wang, J. Zhang, X. Wang, S. Guan, and H. Yu, "Improved BOTSORT multi-object tracking algorithm for robotic rollers using feature-level fusion of millimeter-wave radar and camera sensors," *Inf. Fusion*, vol. 123, Nov. 2025, Art. no. 103294.
- [28] J. Liu et al., "Target-aware dual adversarial learning and a multi-scenario multi-modality benchmark to fuse infrared and visible for object detection," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2022, pp. 5792–5801.
- [29] Y. Cao, X. Luo, J. Yang, Y. Cao, and M. Y. Yang, "Locality guided cross-modal feature aggregation and pixel-level fusion for multispectral pedestrian detection," *Inf. Fusion*, vol. 88, pp. 1–11, Dec. 2022.
- [30] Y. Cao, J. Bin, J. Hamari, E. Blasch, and Z. Liu, "Multimodal object detection by channel switching and spatial attention," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW)*, Jun. 2023, pp. 403–411.
- [31] Y. Zhang, H. Yu, Y. He, X. Wang, and W. Yang, "Illumination-guided RGBT object detection with inter- and intra-modality fusion," *IEEE Trans. Instrum. Meas.*, vol. 72, pp. 1–13, 2023.
- [32] P. Gao, T. Tian, T. Zhao, L. Li, N. Zhang, and J. Tian, "GF-detection: Fusion with GAN of infrared and visible images for vehicle detection at nighttime," *Remote Sens.*, vol. 14, no. 12, p. 2771, Jun. 2022.
- [33] X. Zou, T. Peng, and Y. Zhou, "UAV-based human detection with visible-thermal fused YOLOv5 network," *IEEE Trans. Ind. Inform.*, vol. 20, no. 3, pp. 3814–3823, Mar. 2024.
- [34] F. Qingyun and W. Zhaokui, "Cross-modality attentive feature fusion for object detection in multispectral remote sensing imagery," *Pattern Recognit.*, vol. 130, Oct. 2022, Art. no. 108786.
- [35] C. Jiang et al., "M2FNet: Multi-modal fusion network for object detection from visible and thermal infrared images," *Int. J. Appl. Earth Observ. Geoinf.*, vol. 130, Jun. 2024, Art. no. 103918.
- [36] H. Wang et al., "Cross-modal oriented object detection of UAV aerial images based on image feature," *IEEE Trans. Geosci. Remote Sens.*, vol. 62, 2024, Art. no. 5403021.
- [37] W. Zhao, Z. Zhao, M. Xu, Y. Ding, and J. Gong, "Differential multimodal fusion algorithm for remote sensing object detection through multi-branch feature extraction," *Expert Syst. Appl.*, vol. 265, Mar. 2025, Art. no. 125826.
- [38] Y. Zhang et al., "Drone-based RGBT tiny person detection," *ISPRS J. Photogramm. Remote Sens.*, vol. 204, pp. 61–76, Oct. 2023.
- [39] L. Zhang, X. Zhu, X. Chen, X. Yang, Z. Lei, and Z. Liu, "Weakly aligned cross-modal learning for multispectral pedestrian detection," in *Proc. IEEE/CVF Int. Conf. Comput. Vis. (ICCV)*, Oct. 2019, pp. 5126–5136.
- [40] K. Zhou, L. Chen, and X. Cao, "Improving multispectral pedestrian detection by addressing modality imbalance problems," in *Proc. Eur. Conf. Comput. Vis.*, 2020, pp. 787–803.
- [41] Z. Zhao, W. Zhang, Y. Xiao, C. Li, and J. Tang, "Reflectance-guided progressive feature alignment network for all-day UAV object detection," *IEEE Trans. Geosci. Remote Sens.*, vol. 63, 2025, Art. no. 5404215.
- [42] M. Yuan and X. Wei, "C<sup>2</sup>former: Calibrated and complementary transformer for RGB-infrared object detection," *IEEE Trans. Geosci. Remote Sens.*, vol. 62, 2024, Art. no. 5403712.
- [43] A. Vaswani et al., "Attention is all you need," in *Proc. Neural Inf. Process. Syst.*, vol. 30, 2017, pp. 5998–6008.
- [44] K. Song, X. Xue, H. Wen, Y. Ji, Y. Yan, and Q. Meng, "Misaligned visible-thermal object detection: A drone-based benchmark and baseline," *IEEE Trans. Intell. Vehicles*, vol. 9, no. 11, pp. 7449–7460, Nov. 2024.
- [45] C. Chen et al., "Weakly misalignment-free adaptive feature alignment for UAVs-based multimodal object detection," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2024, pp. 26826–26835.
- [46] J. Dai et al., "Deformable convolutional networks," in *Proc. IEEE Int. Conf. Comput. Vis. (ICCV)*, Oct. 2017, pp. 764–773.
- [47] C. Liu, X. Ma, X. Yang, Y. Zhang, and Y. Dong, "COMO: Cross-mamba interaction and offset-guided fusion for multimodal object detection," *Inf. Fusion*, vol. 125, Jan. 2026, Art. no. 103414.
- [48] W. Bao, M. Huang, J. Hu, and X. Xiang, "Dual-dynamic cross-modal interaction network for multimodal remote sensing object detection," *IEEE Trans. Geosci. Remote Sens.*, vol. 63, 2025, Art. no. 5401013.
- [49] Y. Cao, J. Xu, S. Lin, F. Wei, and H. Hu, "GCNet: Non-local networks meet squeeze-excitation networks and beyond," in *Proc. IEEE/CVF Int. Conf. Comput. Vis. Workshops*, Jun. 2019, pp. 1971–1980.
- [50] J. Xie, J. Nie, B. Ding, M. Yu, and J. Cao, "Cross-modal local calibration and global context modeling network for RGB-infrared remote-sensing object detection," *IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens.*, vol. 16, pp. 8933–8942, 2023.
- [51] Z. Wang, X. Liao, J. Yuan, Y. Yao, and Z. Li, "CDC-YOLOFusion: Leveraging cross-scale dynamic convolution fusion for visible-infrared object detection," *IEEE Trans. Intell. Vehicles*, vol. 10, no. 3, pp. 2080–2093, Mar. 2025.
- [52] T.-Y. Lin, P. Dollár, R. Girshick, K. He, B. Hariharan, and S. Belongie, "Feature pyramid networks for object detection," in *Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jul. 2017, pp. 936–944.
- [53] Z. Liu et al., "Swin transformer: Hierarchical vision transformer using shifted windows," in *Proc. IEEE/CVF Int. Conf. Comput. Vis. (ICCV)*, Oct. 2021, pp. 9992–10002.
- [54] H. Rezatofighi, N. Tsoi, J. Gwak, A. Sadeghian, I. Reid, and S. Savarese, "Generalized intersection over union: A metric and a loss for bounding box regression," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2019, pp. 658–666.
- [55] T.-Y. Lin, P. Goyal, R. Girshick, K. He, and P. Dollár, "Focal loss for dense object detection," in *Proc. IEEE Int. Conf. Comput. Vis. (ICCV)*, Oct. 2017, pp. 2999–3007.

- [56] H. Feng, L. Zhang, S. Zhang, D. Wang, X. Yang, and Z. Liu, "RTDOD: A large-scale RGB-thermal domain-incremental object detection dataset for UAVs," *Image Vis. Comput.*, vol. 140, Dec. 2023, Art. no. 104856.
- [57] X. Yu, Y. Gong, N. Jiang, Q. Ye, and Z. Han, "Scale match for tiny person detection," in *Proc. IEEE Winter Conf. Appl. Comput. Vis. (WACV)*, Mar. 2020, pp. 1246–1254.
- [58] P. Zhang, J. Zhao, D. Wang, H. Lu, and X. Ruan, "Visible-thermal UAV tracking: A large-scale benchmark and new baseline," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2022, pp. 8876–8885.
- [59] T.-Y. Lin et al., "Microsoft COCO: Common objects in context," in *Proc. Eur. Conf. Comput. Vis.*, 2014, pp. 740–755.
- [60] A. Paszke et al., "PyTorch: An imperative style, high-performance deep learning library," 2019, *arXiv:1912.01703*.
- [61] K. Chen et al., "MMDetection: Open MMLab detection toolbox and benchmark," 2019, *arXiv:1906.07155*.
- [62] K. He, X. Zhang, S. Ren, and J. Sun, "Deep residual learning for image recognition," in *Proc. IEEE Conf. Comput. Vis. Pattern Recognit.*, Jun. 2015, pp. 770–778.
- [63] J. Deng, W. Dong, R. Socher, L.-J. Li, K. Li, and L. Fei-Fei, "ImageNet: A large-scale hierarchical image database," in *Proc. IEEE Conf. Comput. Vis. Pattern Recognit.*, Jun. 2009, pp. 248–255.
- [64] S. Zhang, C. Chi, Y. Yao, Z. Lei, and S. Z. Li, "Bridging the gap between anchor-based and anchor-free detection via adaptive training sample selection," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2020, pp. 9756–9765.
- [65] T. Brödermann, C. Sakaridis, D. Dai, and L. Van Gool, "HRFuser: A multi-resolution sensor fusion architecture for 2D object detection," in *Proc. IEEE 26th Int. Conf. Intell. Transp. Syst. (ITSC)*, Sep. 2023, pp. 4159–4166.
- [66] Y. Liu, W. Guo, C. Yao, and L. Zhang, "Dual-perspective alignment learning for multimodal remote sensing object detection," *IEEE Trans. Geosci. Remote Sens.*, vol. 63, 2025, Art. no. 5404015.
- [67] S. Ren, K. He, R. Girshick, and J. Sun, "Faster R-CNN: Towards real-time object detection with region proposal networks," *IEEE Trans. Pattern Anal. Mach. Intell.*, vol. 39, no. 6, pp. 1137–1149, Jun. 2017.
- [68] Z. Cai and N. Vasconcelos, "Cascade R-CNN: High quality object detection and instance segmentation," *IEEE Trans. Pattern Anal. Mach. Intell.*, vol. 43, no. 5, pp. 1483–1498, May 2021.
- [69] Z. Tian, C. Shen, H. Chen, and T. He, "FCOS: Fully convolutional one-stage object detection," in *Proc. IEEE/CVF Int. Conf. Comput. Vis. (ICCV)*, Oct. 2019, pp. 9626–9635.

![Portrait of Minchao Luo](555df5c0300cb1fca5dc028fec5ec6be_img.jpg)

Portrait of Minchao Luo

**Minchao Luo** received the B.S. degree in electronic information engineering from Hunan University of Technology, Zhuzhou, China, in 2023. He is currently pursuing the M.S. degree with Ningbo University, Ningbo, China.

His research interests include visible and infrared image fusion, as well as object detection in remote sensing images.

![Portrait of Rui Zhao](a8e5c2ac336eb43cda4e333ea9c73237_img.jpg)

Portrait of Rui Zhao

**Rui Zhao** (Member, IEEE) received the B.S. degree in remote sensing science and technology from Wuhan University, Wuhan, China, in 2012, and the Ph.D. degree in photogrammetry and remote sensing from the State Key Laboratory of Information Engineering in Surveying, Mapping and Remote Sensing, Wuhan University, in 2017.

He worked as a Post-Doctoral Researcher with the School of Earth and Space Sciences, Peking University, Beijing, China, from 2020 to 2022. He is currently an Associate Researcher with the Faculty of Electrical Engineering and Computer Science, Ningbo University, Ningbo, China. His research interests include remote sensing, image processing, artificial intelligence, pattern recognition, deep learning, and machine learning.

Dr. Zhao serves as a Reviewer for Science Citation Index magazines including IEEE TRANSACTIONS ON NEURAL NETWORKS AND LEARNING SYSTEMS (TNNLS), IEEE TRANSACTIONS ON GEOSCIENCE AND REMOTE SENSING (TGRS), *International Journal of Applied Earth Observation and Geoinformation (JAG)*, IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING (JSTARS), IEEE GEOSCIENCE AND REMOTE SENSING LETTERS (GRSL), and *International Journal of Remote Sensing (IJRS)*.

![Portrait of Shenfu Zhang](4a104be5f84f688417d8c222ec4ce4fa_img.jpg)

Portrait of Shenfu Zhang

**Shenfu Zhang** received the B.S. degree from Shaoxing University, Shaoxing, China, in 2022. He is currently pursuing the Ph.D. degree with Ningbo University, Ningbo, China.

His research interests include hyperspectral image processing and multisource data fusion classification.

![Portrait of Liang Chen](61cb1feb42558ca9da53cfdb7f7386a7_img.jpg)

Portrait of Liang Chen

**Liang Chen** received the B.S. and Ph.D. degrees from the University of Science and Technology of China, Hefei, China, in 2016 and 2023, respectively.

He is currently a Lecturer with the Faculty of Electrical Engineering and Computer Science, Ningbo University, Ningbo, China. His current interests include hyperspectral image processing and target detection.

![Portrait of Feng Shao](7c520d92519c6f446195871b8855178c_img.jpg)

Portrait of Feng Shao

**Feng Shao** (Member, IEEE) received the B.S. and Ph.D. degrees in electronic science and technology from Zhejiang University, Hangzhou, China, in 2002 and 2007, respectively.

He was a Visiting Fellow with the School of Computer Engineering, Nanyang Technological University, Singapore, from 2012 to 2012. He is currently a Professor with the Faculty of Information Science and Engineering, Ningbo University, Ningbo, China. He has published over 100 technical articles in refereed journals and proceedings in the areas of 3-D video coding, 3-D quality assessment, and image perception.

Dr. Shao received the Excellent Young Scholar Award from the NSF of China (NSFC), in 2016.

![Portrait of Xiangchao Meng](c1b31d4aff04545839dcaa17acf93363_img.jpg)

Portrait of Xiangchao Meng

**Xiangchao Meng** (Senior Member, IEEE) received the B.S. degree in geographic information system from Shandong University of Science and Technology, Qingdao, China, in 2012, and the Ph.D. degree in cartography and geography information system from Wuhan University, Wuhan, China, in 2017.

He worked as a Post-Doctoral Researcher with the College of Electrical and Information Engineering, Hunan University, Changsha, China. He is currently a Professor with the Faculty of Electrical Engineering and Computer Science, Ningbo University, Ningbo, China. His research interests include multisource data fusion and machine learning.