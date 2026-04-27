

<!-- Page 1 -->

## A Progressive Spatial–Spectral Interactive Network for Integrated Fusion of Panchromatic, Multispectral, and Hyperspectral Images

Yufu Bai, Minchao Luo, Shenfu Zhang, Qiang Liu [,](https://orcid.org/0000-0002-9966-7803) Liang Che[n](https://orcid.org/0000-0002-2974-8616) , Weiwei Sun [,](https://orcid.org/0000-0003-3399-7858) *Senior Member, IEEE*, and Xiangchao Meng [,](https://orcid.org/0000-0002-7405-3143) *Senior Member, IEEE*

*Abstract*—Satellite-based hyperspectral (HS) imagery holds great potential in remote sensing applications due to its fine spectral resolution. However, the low spatial resolution limits its practical utility. Combining ancillary high-resolution (HR) panchromatic (PAN) or multispectral (MS) images has become a common practice to improve the spatial quality of HS images. Most present approaches, however, are based on dual-sensor fusion (e.g., MS–HS or PAN–HS), which generally falls short of comprehensively integrating their complementary spatial and spectral information of PAN, MS, and HS images. Meanwhile, the existing few integrated fusion methods suffer from two key limitations: modality mismatch due to inconsistent spatial–spectral characteristics among PAN, MS, and HS data, and shallow and redundant cross-modal coupling caused by inadequate modeling of intermodal relationships. In this article, we propose a progressive spatial–spectral interactive network (PSSNet) for the integrated fusion of PAN, MS, and HS images. Specifically, a context-aware fusion block (CAFB) is introduced to extract and enhance contextual spatial and spectral information across different modalities. To ensure an effective integration of spatial and spectral details, the entire network is structured progressively, allowing for a smooth transition and fusion of features from HS, MS, and PAN images. Additionally, a spatial–spectral feature recombination module (SSRM) is designed to dynamically adjust the contribution of spectral features at various levels. This module, in combination with a spatial enhancement component, facilitates the optimal fusion of spatial and spectral information by enhancing their interactions. Extensive experiments on simulated and real datasets, both qualitatively and quantitatively, demonstrate the superiority of PSSNet compared to other stateof-the-art methods.

*Index Terms*—Hyperspectral (HS) image, integrated fusion, multispectral (MS) image, panchromatic (PAN) image.

Received 11 May 2025; revised 10 July 2025; accepted 11 August 2025. Date of publication 18 August 2025; date of current version 19 September 2025. This work was supported in part by Zhejiang Provincial Natural Science Foundation of China under Grant LR23D010001, in part by the National Natural Science Foundation of China under Grant 42171326, and in part by Ningbo Natural Science Foundation under Grant 2022J076. *(Corresponding author: Xiangchao Meng.)*

Yufu Bai, Minchao Luo, Shenfu Zhang, Liang Chen, and Xiangchao Meng are with the Faculty of Electrical Engineering and Computer Science, Ningbo University, Ningbo 315211, China (e-mail: baiyufu2001@126.com; 2311100052@nbu.edu.cn; zhangshenfu nbu@163.com; chenliang4@nbu. edu.cn; mengxiangchao@nbu.edu.cn).

Qiang Liu is with the School of Computer and Artificial Intelligence, Huanghuai University, Zhumadian 463000, China (e-mail: qiangliu0722@163.com).

Weiwei Sun is with the Department of Geography and Spatial Information Techniques, Ningbo University, Ningbo 315211, China (e-mail: sunweiwei@nbu.edu.cn).

Digital Object Identifier 10.1109/TGRS.2025.3599879

## I. INTRODUCTION

S PACEBORNE hyperspectral (HS) images with both high spatial and high spectral resolutions are highly desirable in large-scale fine-resolution applications, such as precision agriculture, wetland mapping, and environmental quantitative inversion [1], [2]. However, HS images generally face the issue of low spatial resolution due to limitations in optical sensor hardware. In contrast, multispectral (MS) and panchromatic (PAN) images offer higher spatial resolution but with fewer spectral bands. Therefore, HS image fusion has emerged as a promising solution, aiming to combine the spectral richness of HS images with the spatial details of MS or PAN images to generate high spatial resolution HS images. These fusion methods can be categorized into three main types: PAN–HS fusion, MS–HS fusion, and PAN–MS–HS fusion.

The goal of PAN–HS fusion is to improve the spatial resolution of HS images by utilizing PAN images, whereas MS–HS fusion leverages MS images to enhance the spatial resolution of HS images. In contrast, PAN–MS–HS fusion aims to integrate the complementary spatial and spectral strengths of PAN, MS, and HS images, ultimately producing optimal high-resolution (HR) HS images. Among these, PAN–MS–HS fusion is particularly promising but more challenging due to the distinct spatial and spectral characteristics of the image types involved. The combination of HR PAN images, relative "medium"-resolution (MR) MS images, and lowresolution (LR) HS images presents a unique opportunity to leverage their complementary information. However, the key challenge lies in how to effectively integrate these disparate data sources. Unlike single-modality hierarchical networks (e.g., U-Net and ResNet) that process homogeneous data through symmetric pathways, PAN–MS–HS fusion requires: modality-specific feature extraction, cross-modal progressive refinement to prevent distortion accumulation, and dynamic interaction mechanisms to avoid shallow feature coupling.

Generally, existing PAN–MS–HS fusion strategies can be broadly categorized into three types: step-by-step fusion, information injection-based fusion, and feature concatenation-based fusion.

The step-by-step fusion approach is one intuitive method in which the relative "MR" MS is fused with the LR HS to generate an "MR" HS image, as shown in Fig. 1(a). Then, the "MR" HS is fused with the HR PAN to obtain the final HR HS. However, this approach introduces a pseudo-intermediate result, i.e., the MR HS, which splits a unified process into two

1558-0644 © 2025 IEEE. All rights reserved, including rights for text and data mining, and training of artificial intelligence and similar technologies. Personal use is permitted, but republication/redistribution requires IEEE permission. See https://www.ieee.org/publications/rights/index.html for more information.

<!-- Page 2 -->

Fig. 1. Schematic of the existing PAN–MS–HS fusion methods. (a) Step-by-step fusion. (b) Information injection-based fusion. (c) Feature concatenation-based fusion.

steps. Therefore, if there is any spatial or spectral distortion in either step, it will lead to significant distortion in both the spatial and spectral information of the final fused result. If PAN and MS are fused first, a similar issue arises, resulting in distortions in the final result.

The information injection-based fusion approach directly injects the extracted information from PAN and MS into the HS to generate the final HR HS, as shown in Fig. 1(b). While this method can enhance the spatial resolution, it suppresses the rich spectral information, inevitably causing spectral distortion. Additionally, it fails to adequately capture the contextual relationships between different modalities, making it difficult to combine rich spectral features with spatial details, which negatively affects the fusion outcome.

The feature concatenation-based fusion approach aggregates or concatenates the features from all three modalities and then performs feature learning and reconstruction, as shown in Fig. 1(c). However, this fusion method introduces feature redundancy across different modalities, which negatively impacts the model's learning performance. It also ignores the contextual information between modalities and fails to utilize the original shallow spatial and spectral features effectively, thus struggling to capture the correlations and spatial structure between the modalities. Therefore, achieving a good balance between spatial and spectral qualities in the fusion of PAN, MS, and HS remains a challenging task.

While the advancements in PAN–MS–HS fusion methods are notable, they still face significant issues when it comes to fully leveraging the complementary spatial and spectral information from HR PAN, MR MS, and LR HS images. Specifically, two major issues remain in achieving optimal PAN–MS–HS fusion.

## *A. Issue 1: Modality Mismatch*

Existing methods exhibit deficiencies in addressing the intrinsic characteristic differences among PAN, MS, and HS images. The cross-scale feature inconsistency among PAN, MS, and HS leads to spectral contamination and spatial blurring issues. For example, the texture details of MS may overwhelm the weak spectral responses of HS. Meanwhile, single-branch architectures and injection-based architectures exacerbate these problems due to the lack of adaptive cross-resolution modulation capabilities. This results in the accumulation of spectral distortion or spatial artifacts in the fusion results.

## *B. Issue 2: Shallow and Redundant Cross-Modal Coupling*

Most current methods are limited by shallow crossmodal interactions and redundant feature entanglement in the spectral–spatial domain. They rely on relatively direct feature concatenation or simple attention mechanisms. There is a lack of in-depth modeling of local spatial–spectral dependencies, which fails to distinguish the weights of different features and introduces invalid features that cause interference.

To address Issue 1, we design differentiated feature extraction pathways and a progressive hierarchical fusion framework to resolve cross-scale inconsistencies and spectral–spatial conflicts. Specifically, for a high spatial resolution PAN image, we employ edge-optimized convolutional blocks to preserve geometrical details, while HS images are processed via spectral–spatial convolutions to capture fine-grained spectral correlations. Unlike MGFEI-Net's simultaneous multiscale grouping fusion, which may cause feature conflicts across resolutions, our progressive framework (HS→MS→PAN) enables hierarchical spatial–spectral alignment. The network progressively integrates HS, MS, and PAN features through adaptive cross-modal modulation, where each layer dynamically calibrates resolution disparities (e.g., suppressing PAN texture dominance over HS spectra) via residual-optimized modulation. This ensures gradual refinement, where intermediate features are optimized through residual connections to prevent spatial blurring and spectral distortion accumulation.

To tackle Issue 2, we propose a context-aware fusion block (CAFB) with cross-modal attention and a spectral–spatial recombination module with dynamic gating. In CAFB, highspatial features guide queries to attend to HS spectral keys, enabling deep interaction without redundancy and dynamically adjusting the contribution of different modalities via query–key

<!-- Page 3 -->

attention. In addition, the CAFB captures long-range dependencies, avoiding shallow feature mixing. In spatial–spectral feature recombination module (SSRM), the dynamic spectral adjustment module (DSAM) uses channel attention to suppress redundant spectral bands and enhance discriminative features, while spatial prior enhancement unit (SPEU) extracts PANguided spatial priors via dual-pooling.

The main contributions of this study are summarized as follows.

- 1) We propose a progressive spatial–spectral interactive network (PSSNet) that effectively handles the fusion of PAN, MS, and HS images through modality-specific processing and adaptive cross-modal interaction. The network achieves high-fidelity HR HS images by intelligently combining complementary spatial and spectral information.
- 2) A progressive fusion architecture is developed to gradually integrate information from HS, MS, and PAN images. This hierarchical approach dynamically aligns spatial resolutions and suppresses spectral contamination through residual-optimized modulation, improving both spatial detail preservation and spectral fidelity.
- 3) Two key components are introduced: a CAFB employing cross-modal attention to enable deep spatial–spectral interactions while avoiding feature redundancy, and a spectral–spatial recombination module that dynamically reweights spectral features and enhances spatial details through channel attention and PAN-guided refinement, effectively eliminating shallow feature entanglement.

The rest of this article is structured as follows. Section II introduces the related work. Section III provides a detailed explanation of the proposed PSSNet. Section IV presents a comprehensive analysis of the experiments conducted to demonstrate the effectiveness of our approach. Section V offers an in-depth discussion on the contributions to core modules, the ablation study, and efficiency comparison. Finally, the conclusion is summarized in Section VI.

## II. RELATED WORK

## *A. PAN–HS Fusion*

Traditional PAN–HS fusion methods derive from standard pansharpening methods (i.e., PAN–MS fusion) [3], [4], [5]; PAN–HS fusion is often referred to as HS pansharpening. PAN–HS fusion algorithms can generally be classified into component substitution (CS), multiresolution analysis (MRA), model-based optimization, and deep learning methods [6], [7].

CS and MRA methods primarily aim to extend classical pansharpening techniques. The CS-based methods transform the HS image into a domain that separates spatial and spectral components, and then use the PAN image to replace the spatial component of the HS image, followed by an inverse transformation to obtain the PAN–HS fusion result. Typical transformation methods include intensity–hue–saturation (IHS), principal component analysis (PCA), and Gram–Schmidt (GS) [8], [9], [10], [11]. MRA-based methods, on the other hand, first extract the spatial details of the PAN data and inject them into the resampled HS image through multiresolution decomposition to obtain HR HS images. Examples include wavelet transform, modulation transfer function generalized Laplacian pyramid (MTF-GLP), and morphological filters [12], [13], [14]. While CS-based methods perform well in spatial performance, they often lead to significant spectral distortion. MRA-based methods, due to the difficulty of designing ideal spatial filters, are usually complex to implement accurately [7].

In model-based optimization methods, Bayesian estimationbased approaches [15], [16] derive probabilistic parameters through Bayesian statistics and apply them to HS pansharpening. Variational optimization-based methods [17] attempt to use variational theory to reconstruct the target image, often involving ill-posed inverse problems to model HS pansharpening. These methods require prior knowledge and reasonable assumptions for image reconstruction. The representation power of the adopted model greatly affects the fusion results, and when assumptions do not align with the problem, the quality of the fused image can deteriorate significantly.

In recent years, deep learning has gained increasing attention in PAN–HS fusion due to its excellent feature extraction and nonlinear representation capabilities. He et al. [18] proposed a spectral prediction convolutional neural network (HyperPNN) to enhance the spatial resolution of HS images. Wang et al. [19] proposed a dual Gaussian–Laplacian pyramid and transformer multiscale fusion network (MDTP-Net) to address spectral distortion and insufficient spatial texture enhancement. Guarino et al. [20] proposed a sequential bandwise adaptive scheme to tackle issues arising from the scarcity and diversity of training data. He et al. [21] introduced a dynamic fusion convolutional neural network (DyPNNs), which uses adaptive spatial modulation to address the problem of static fusion methods being unable to handle spatial variations in HS data.

## *B. MS–HS Fusion*

Existing MS–HS fusion methods can be mainly categorized into CS, MRA, matrix factorization (MF), tensor representation (TR), and deep learning-based methods [22], [23]. CSand MRA-based methods also stem from traditional pansharpening methods. For example, Selva et al. [24] proposed a fusion framework that linearly regresses each HS band's HR image as a linear combination of the MS bands, effectively adapting MRA-based methods to MS–HS fusion.

MF-based methods decompose the target HR HS image into a spectral basis matrix and a coefficients matrix, and then estimate the spectral basis and coefficients matrix using the observed LR HS and HR MS information in various ways to obtain the fusion result. For instance, Kawakami et al. [25] proposed a sparse matrix factorization (SMF) method, estimating the spectral basis using sparse dictionary learning and obtaining sparse coefficients with sparse coding algorithms. Akhtar et al. [26] learned the spectral dictionary from LR HS images and estimated coefficients from HR MS images using Bayesian sparse coding. Additionally, Yokoya et al. [27] used coupled nonnegative matrix factorization (CNMF) to solve the spectral unmixing problem by alternately updating the spectral basis and coefficients. Lanaras et al. [28] applied multiple priors for spectral unmixing and used proximal alternating linearized minimization to obtain the spectral basis and coefficients. These methods directly benefit from specific observation models but tend to be sensitive

<!-- Page 4 -->

to parameters and computationally expensive when solving complex optimization problems.

TR-based methods treat images as tensors to preserve their spatial and spectral structures, rather than reshaping images into matrix forms. For example, Li et al. [29] proposed a coupled sparse tensor factorization (CSTF) method that estimates dictionaries and core tensors through alternating optimization. Dian et al. [30] introduced a nonlocal sparse tensor factorization method (NLSTF SMBF) to effectively fuse MS and HS images in semiblind scenarios. Xu et al. [31] used coupled tensor canonical polyadic (CP) decomposition to decompose HR HS images and applied alternating direction method of multipliers to enhance the spatial resolution of LR HS images. Furthermore, He et al. [32] proposed a coupled tensor ring factorization (CTRF) model to learn HR HS tensor ring core tensors and improve spatial resolution and spectral fidelity through spectral nuclear-norm regularization. However, TR-based methods still face challenges with high computational complexity and the need for accurate estimation of the point spread function (PSF) and spectral response function (SRF) [22].

Deep learning-based approaches for MS-HS fusion have been gaining popularity. Sun et al. [33] proposed a deep learning-based domain transformation model (DTAFN) that achieves high-quality noise-robust fusion of MS and HS images through wavelet decomposition and spatial-spectral self-attention mechanisms. Wang et al. [34] introduced a spatial-spectral implicit neural representation (SS-INR) network that performs high-quality fusion of HS and MS images using spatial-INR and spectral-INR, overcoming resolution discrepancies and effectively recovering continuous information. In addition, to better extract spatial and spectral features from limited training data and better adapt to real-world data fusion, some unsupervised fusion networks have emerged in recent years. Cao et al. [35] proposed an unsupervised hybrid network model (uHNTC), combining transformers and convolutional neural networks, and achieving high-quality blind HS and MS image fusion through multilevel crossfeature attention mechanisms. Liu et al. [36] introduced an unsupervised lightweight attention cyclic network (Circle-Net), which achieves efficient fusion of HS and MS images through coordinate feature fusion and dual-attention decoding.

## C. PAN-MS-HS Fusion

In contrast to approaches for fusing two types of pictures, the fusion of PAN, MS, and HS images intends to fully integrate spectral and spatial information from HR PAN, MR MS, and LR HS images to yield the goal HR HS image. In recent years, there have been several studies on PAN-MS-HS fusion methods. Yokoya et al. [37] suggested a CNMF approach for fusing PAN, MS, and HS images. Meng et al. [38] introduced an HS image fusion method based on the MAP framework, which utilizes multisource data to enhance spatial and spectral information, addressing fusion issues under large resolution differences. Bendoumi and Benlefki [39] proposed an unconstrained least-squares unmixing method that extracts spatial and spectral features through unmixing formulas to generate high spatial resolution HS images. Arablouei [40] addressed the PAN-MS-HS fusion task using endmember and abundance estimation combined with regularization methods. Tian et al. [41] established a data fidelity term and prior constraints to preserve the spatial and spectral information of HS and MS, using the structural similarity (SSIM) of PAN to transfer spatial details and improve the spatial resolution of HS images. However, these methods often fail to consider all aspects when designing artificial parameters and prior constraints, which affects the fusion results.

With the advancement of deep learning in various computer vision tasks, especially in remote sensing image fusion [42], [43], [44], deep learning-based methods are also gaining attention in PAN–MS–HS fusion. Li et al. [45] were the first to introduce deep learning into the fusion of PAN, MS, and HS images. Meng et al. [46], considering the limitations of actual imaging devices, proposed an integrated fusion method for PAN, MS, and HS images with different imaging bandwidths. Tian et al. [47] proposed an interpretable model-driven deep network that integrates optimization-solving models and deep priors into network modules for PAN, MS, and HS image fusion. Additionally, Meng et al. [48] proposed a top–down multiscale grouping feedback embedded integration fusion network to address the challenge of large spatial resolution differences in PAN–MS–HS fusion.

## III. PROPOSED METHOD

The ideal HR HS is defined as  $\mathbf{Z} \in \mathbb{R}^{H \times W \times C}$ , where H and W represent the height and width, respectively, and C denotes the number of spectral bands. HR PAN can be represented as  $\mathbf{P} \in \mathbb{R}^{H \times W \times 1}$ . MR MS is defined as  $\mathbf{M} \in \mathbb{R}^{h_0 \times w_0 \times c}$ , where  $h_0 = H/s_0$  and  $w_0 = W/s_0$  are the spatial dimensions of MR MS,  $s_0$  is the spatial resolution ratio between HR HS and MR MS, and c represents the number of spectral bands in MS. The observed LR HS is defined as  $\mathbf{H} \in \mathbb{R}^{h_1 \times w_1 \times C}$ , where the spatial dimensions of LR HS are  $h_1 = H/s_1$  and  $w_1 = W/s_1$ , and  $s_1$  is the spatial resolution ratio between LR HS and HR HS. Our goal is to obtain a fused image  $\mathbf{Z}$ , which should have the high spatial resolution of the HR PAN image and the rich spectral information of the LR HS image.

The overall network structure of PSSNet is shown in Fig. 2, which consists of four main components: primary feature extraction module, CAFB, spatial–spectral recombination module, and feature reconstruction block. First, the three input modalities—PAN, MS, and HS—are passed through their respective independent primary feature extractors to obtain the primary features. These features are, then, progressively fed into the CAFB, SSRM, and feature reconstruction (RE) modules through a structure that combines progressive and skip connections.

## A. Primary Feature Extraction Module

HS images contain rich spectral information, which is most notably reflected in the large number of spectral bands. PAN images have more spatial geometrical structure, while MS images possess both medium spectral information and spatial detail. The three input images are passed through their respective feature extraction modules with nonshared weights to obtain primary features. The goal is to extract modality-specific features and unify different scales. The process can be expressed as follows:

$$CBRE(\mathbf{F}_{in}) = ReLU(BN(Conv_{3\times3}(\mathbf{F}_{in})))$$
 (1)

<!-- Page 5 -->

Fig. 2. Overall architecture diagram of the proposed method.

$$Conv_{res}(\mathbf{F}_{in}) = ReLU\left(BN\left(Conv_{3\times3}\left(CBRE\left(\mathbf{F}_{in}\right)\right)\right) + \mathbf{F}_{in}\right)$$
(2)

$$\mathbf{F}_{hs}^{0} = CBRE\left(\mathrm{Up}\left(\mathrm{Conv}_{1\times 1}\left(\mathbf{H}\right)\right)\right) \tag{3}$$

$$\mathbf{F}_{ms}^{0} = \text{Up}\left(\text{Conv}_{3\times3}\left(\text{ReLU}\left(\text{Conv}_{3\times3}\left(\text{Conv}_{\text{res}}\left(\mathbf{M}\right)\right)\right)\right)\right)$$

$$\mathbf{F}_{\text{nan}}^{0} = CBRE \left( \text{Conv}_{\text{res}} \left( \mathbf{P} \right) \right) \tag{5}$$

where  $CBRE(\cdot)$  represents the sequential combination of a convolution layer with a 3  $\times$  3 kernel, a batch normalization layer, and an ReLU activation function.  $Conv_{res}(\cdot)$  refers to a basic structure in ResNet.  $Conv_{1\times 1}(\cdot)$  denotes a convolution layer with a 1  $\times$  1 kernel, and  $Up(\cdot)$  indicates the upsampling operation.

## B. Context-Aware Fusion Block

Unlike general image vision tasks, improving the spatial resolution of HS images is not simply a matter of image upscaling, but requires an organic fusion of both spatial and spectral information. This is because HS images contain a large number of spectral bands, which have complex spatial–spectral dependencies. Traditional approaches, such as concatenation followed by convolution, often fail to effectively capture the contextual information between these spatial–spectral relationships, resulting in suboptimal fusion outcomes.

To address this issue, we propose a context-aware fusion module that combines the shifted window attention mechanism of the Swin Transformer with a cross-modal attention mechanism. The structure is illustrated in Fig. 3.

The main component of this module is based on the crossattention mechanism with windows and shifted windows. In the Swin Transformer, for a given feature  $\mathbf{F} \in \mathbb{R}^{H \times W \times C}$ , the feature is first divided using an  $M \times M$  window, splitting it into  $HW/M^2$  nonoverlapping patches, each of shape  $M \times M \times C$ , which are then flattened into  $M^2 \times C$ , where  $HW/M^2$  represents the total number of windows. Next, standard self-attention operations are performed within each window. For the feature  $\mathbf{X} \in \mathbb{R}^{M^2 \times C}$  within a window, three learnable weight matrices,  $\mathbf{W}^Q \in \mathbb{R}^{C \times C}$ ,  $\mathbf{W}^k \in \mathbb{R}^{C \times C}$ , and  $\mathbf{W}^V \in \mathbb{R}^{C \times C}$ , are shared across windows to map the features into query, key, and value matrices, namely,  $\mathbf{O}$ ,  $\mathbf{K}$ , and  $\mathbf{V}$ 

$$\mathbf{O} = \mathbf{X}\mathbf{W}^{Q}, \ \mathbf{K} = \mathbf{X}\mathbf{W}^{K}, \ \mathbf{V} = \mathbf{X}\mathbf{W}^{V}.$$
 (6)

Then, the attention function primarily calculates the matrix product of the query and the transpose of the key, followed by a softmax operation to normalize the result and obtain the attention scores, which are then multiplied by the value. The attention mechanism is defined as

**Attention** = softmax 
$$\left(\mathbf{Q}\mathbf{K}^{T}/\sqrt{D} + \beta\right)\mathbf{V}$$
 (7)

where D is the dimensionality of  $\mathbf{Q}$  and  $\mathbf{K}$ , and  $\beta$  is the learnable relative position encoding.

Building upon this, we introduce cross-attention, where two input features,  $\mathbf{F}_1 \in \mathbb{R}^{H \times W \times C}$  and  $\mathbf{F}_2 \in \mathbb{R}^{H \times W \times C}$ , are simultaneously divided into nonoverlapping subwindows using an  $\mathbf{M} \times \mathbf{M}$  window. For the features  $\mathbf{X}_1 \in \mathbb{R}^{M^2 \times C}$  and  $\mathbf{X}_2 \in \mathbb{R}^{M^2 \times C}$  within each window,  $\mathbf{X}_1$  is used to map to the key and value matrices via learnable weight matrices, while  $\mathbf{X}_2$  is mapped to the query matrix. Finally, the attention results are computed uniformly. This process can be expressed as

$$\mathbf{Q}_2 = \mathbf{X}_2 \mathbf{W}^{\mathcal{Q}}, \ \mathbf{K}_1 = \mathbf{X}_1 \mathbf{W}^K, \ \mathbf{V}_1 = \mathbf{X}_1 \mathbf{W}^V$$
 (8)

**Attention** = softmax 
$$\left(\mathbf{Q}_{2}\mathbf{K}_{1}^{T}/\sqrt{D} + \beta\right)\mathbf{V}_{1}$$
. (9)

However, there is no connection between different windows, so after the window attention, a shifted window attention is applied. This involves shifting the windows by  $\lfloor M/2 \rfloor$  pixels.

<!-- Page 6 -->

Fig. 3. Schematic of CAFB. (a) CAFB. (b) W-MCA

Fig. 4. Illustration of the shifted window mechanism for computing attention in the Swin Transformer.

Fig. 4 shows an example of how shifted window attention is calculated in the Swin Transformer.

Next, the specific module flow is illustrated using the left-hand side CAFB-1 depicted in Fig. 2 as an example. The input HS and MS primary features,  $\mathbf{F}_{hs}^0$  and  $\mathbf{F}_{ms}^0$ , respectively, undergo pre-encoding via 3-D convolution and standard convolution

$$\mathbf{F}_{hs}^{1} = \operatorname{Conv}_{3D}\left(\mathbf{F}_{hs}^{0}\right), \ \mathbf{F}_{ms}^{1} = \operatorname{Conv}_{3\times3}\left(\mathbf{F}_{ms}^{0}\right)$$
 (10)

where  $Conv_{3D}(\cdot)$  represents a 3-D convolution layer with a kernel size of  $3 \times 3 \times 3$ , and  $Conv_{3\times 3}(\cdot)$  represents a standard convolution layer with a kernel size of  $3 \times 3$ . The flexible 3-D convolutional kernel structure is more effective in compressing redundancy and capturing spatial–spectral co-occurring features of HS data. This allows for better integration with the spatial features of the MS data in the next step.

The encoded features,  $\mathbf{F}_{hs}^1$  and  $\mathbf{F}_{ms}^1$ , are used as follows: the spectrally rich feature  $\mathbf{F}_{hs}^1$  is used to compute  $\mathbf{K}_1$  and  $\mathbf{V}_1$  in the cross-attention mechanism, while the spatially rich feature  $\mathbf{F}_{ms}^1$  is used to compute  $\mathbf{Q}_2$  in the same mechanism. Therefore,  $\mathbf{Q}_2$  carries the spatial information from  $\mathbf{F}_{ms}^1$ . This spatial detail can provide spatial guidance for the spectral information in  $\mathbf{F}_{hs}^1$ .

At the same time, the cross-attention mechanism, by matching  $\mathbf{Q}_2$  with  $\mathbf{K}_1$ , allows  $\mathbf{F}_{hs}^1$  to incorporate spatial details based on its spectral information, thus improving its spatial resolution

$$\begin{cases} \mathbf{F}_{w}^{0} = W - MCA\left(\mathbf{F}_{hs}^{1}, \mathbf{F}_{ms}^{1}\right) + \mathbf{F}_{hs}^{0} \\ \mathbf{F}_{w}^{1} = MLP\left(LN\left(\mathbf{F}_{w}^{0}\right)\right) + \mathbf{F}_{w}^{0} \end{cases}$$
(11)

$$\mathbf{F}_{sw}^{0} = SW - MCA\left(\mathbf{F}_{w}^{1}, \mathbf{F}_{ms}^{0}\right) + \mathbf{F}_{w}^{1}$$

$$\mathbf{F}_{sw}^{1} = MLP\left(LN\left(\mathbf{F}_{sw}^{0}\right)\right) + \mathbf{F}_{sw}^{0}$$
(12)

where  $LN(\cdot)$  represents the layer normalization operation,  $MLP(\cdot)$  consists of two fully connected layers and a GELU activation function,  $W-MCA(\cdot)$  denotes window-based multihead cross-attention (W-MCA), and  $SW-MCA(\cdot)$  represents shifted window multihead cross-attention. Meanwhile, the window size is 7 and the number of attention heads is 4.

The process of CAFB-2 is similar to that of CAFB-1. That is, the feature  $\mathbf{F}_{sw}^1$  output from CAFB-1, along with the primary feature  $\mathbf{F}_{pan}^0$ , is fed into CAFB-2 to obtain the intermediate feature  $\mathbf{F}_{M}$ .

## Algorithm 1 W-MCA

**Require:**  $\mathbf{F}_{hs}^1 \in \mathbb{R}^{H \times W \times C}$ ,  $\mathbf{F}_{ms}^1 \in \mathbb{R}^{H \times W \times C}$ , window size M = 7

1: Split  $\mathbf{F}_{hs}^1$ ,  $\mathbf{F}_{ms}^1$  into M × M non-overlapping windows

2: **for** each window  $\mathbf{X}_1$  (from  $\mathbf{F}_{hs}^1$ ) and  $\mathbf{X}_2$  (from  $\mathbf{F}_{ms}^1$ ) **do** 

3: Compute  $\mathbf{Q}_2 = \mathbf{X}_2 \mathbf{W}^Q$ ,  $\mathbf{K}_1 = \mathbf{X}_1 \mathbf{W}^K$ ,  $\mathbf{V}_1 = \mathbf{X}_1 \mathbf{W}^V$ 

4: **Attention** = softmax( $\mathbf{Q}_2\mathbf{K}_1^T/\sqrt{D} + \beta$ ) $\mathbf{V}_1$ 

5: end for

6:  $\mathbf{F}_{out} = Window reverse(Attention_1, ..., Attention_h)$ 

7: **return**  $\mathbf{F}_{\text{out}} + \mathbf{F}_{hs}^0$ 

## C. Spatial-Spectral Feature Recombination Module

After the above process, although the intermediate feature  $\mathbf{F}_{M}$  contains multimodal information after passing through the

<!-- Page 7 -->

Fig. 5. Architecture of the spatial-spectral feature recombination module. (a) SSRM. (b) SPAE. (c) DSAM.

context-aware fusion module, further enhancement of shallow information utilization is still needed to achieve a deeper fusion of spatial and spectral information. Specifically, the integration of spatial details and spectral features must be strengthened to improve the accuracy and quality of the final fusion result.

To address this, we propose the spatial–spectral feature recombination module, which includes the DSAM and the CAFB without preconvolution (CAFBL). The overall structure is shown in Fig. 5. The specific module process is illustrated using the right-hand side SSRM-1 in Fig. 2 as an example.

Common methods for fusing different features usually include concatenation followed by a convolution operation or direct summation. However, these simple feature aggregation methods do not recognize important spectral information or perform dynamic adjustments. Inspired by the excellent work of SK-Networks [49], we introduce selective attention in DSAM to adaptively fuse features from different levels.

As shown in Fig. 5,  $\mathbf{F}_{M}$  and  $\mathbf{F}_{ms}^{0}$  are aggregated through a residual structure to form the upper branch's features. Then,  $\mathbf{F}_{ms}^{0}$  is separately processed through a convolution to form the second branch's features. The features are then aggregated through an elementwise summation. Afterward, a global average pooling operation is applied to the summed feature map along the spatial dimension to generate a channel vector. This vector is fed into a fully connected layer to compress the channels, and then, the channels are restored through two separate fully connected layers, generating two channel vectors. Finally, the softmax function is applied to produce complementary selective weights, which are applied to recalibrate and recombine features from the two input branches, dynamically adjusting and reassembling

the spectral features

$$\begin{cases} \mathbf{F}_{d}^{1} = \operatorname{Conv}_{3\times3} \left( \operatorname{Conv}_{\operatorname{res}} \left( \operatorname{Cat} \left( \mathbf{F}_{M}, \mathbf{F}_{ms}^{0} \right) \right) \right) \\ \mathbf{F}_{d}^{2} = \operatorname{Conv}_{1\times1} \left( \mathbf{F}_{ms}^{0} \right) \end{cases}$$
(13)

$$\begin{cases} W^{1} = FC_{1} \left( FC \left( \text{GAP} \left( \mathbf{F}_{d}^{1} + \mathbf{F}_{d}^{2} \right) \right) \right) \\ W^{2} = FC_{2} \left( FC \left( \text{GAP} \left( \mathbf{F}_{d}^{1} + \mathbf{F}_{d}^{2} \right) \right) \right) \end{cases}$$

$$(14)$$

$$\begin{cases} W_{s}^{1}, W_{s}^{2} = \operatorname{softmax}(W^{1}, W^{2}) \\ W_{s_{i}}^{1} = \frac{e^{W_{i}^{1}}}{e^{W_{i}^{1}} + e^{W_{i}^{2}}} \\ W_{s_{i}}^{2} = \frac{e^{W_{i}^{2}}}{e^{W_{i}^{1}} + e^{W_{i}^{2}}} \end{cases}$$
(15)

$$\mathbf{F}_D = W_s^1 * \mathbf{F}_d^1 + W_s^2 * \mathbf{F}_d^2 \tag{16}$$

where the concatenation operation, global average pooling function, and fully connected layer are denoted by  $Cat(\cdot)$ ,  $GAP(\cdot)$ , and  $FC(\cdot)$ , respectively. The compression ratio of the FC layer is 16. The softmax operation is applied to the elements at the corresponding positions of vectors  $\mathbf{W}^1$  and  $\mathbf{W}^2$ .  $W^1_{s_i}$  ( $W^2_{s_i}$ ) and  $W^1_i$  ( $W^2_i$ ) represent the elements in vectors  $W^1_s$  ( $W^2_s$ ) and  $W^1_s$  ( $W^2_s$ ), respectively.  $W^1_s$  and  $W^2_s$  represent the weights of the two branch features.

The goal of using DSAM is to dynamically adjust the features so that the spectral information is recalibrated and recombined, thereby strengthening the spectral information that was lost in previous processing stages. Meanwhile, the differences between modalities in SSRM are reduced, and the complementary spatial and spectral information is unified and aggregated. However, more refined spatial features still exhibit some loss, so the primary feature of the PAN image is used to further optimize the spatial aspects of  $\mathbf{F}_D$ .

<!-- Page 8 -->

Fig. 6. Illustration of feature reconstruction module.

First, a spatial feature enhancement module (SPAE), composed of pooling and self-guided forms, is used to extract spatial information from  $\mathbf{F}_{pan}^0$ . Then, the CAFBL maps the spatial information into  $\mathbf{Q}_2$ . This process adjusts and corrects the features after the DSAM, allowing the spatially refined features to be integrated

$$\mathbf{F}_{\text{spae}} = \text{sigmoid} \left( \text{Conv}_{3\times3} \left( Pavg \left( \mathbf{F}_{\text{pan}}^{0} \right) \right. \right. \\ \left. + Pmax \left( \mathbf{F}_{\text{pan}}^{0} \right) \right) \right) \otimes \mathbf{F}_{\text{pan}}^{0} \qquad (17)$$

$$\mathbf{F}_{R}^{0} = CAFBL \left( \mathbf{F}_{\text{spae}}, \mathbf{F}_{D} \right) \qquad (18)$$

where  $Pavg(\cdot)$  and  $Pmax(\cdot)$  represent the average pooling operation and the max pooling operation, respectively.  $\otimes$  denotes the elementwise multiplication, and  $CAFBL(\cdot)$  represents the CAFB with preconvolution removed. The reason for using CAFBL instead of CAFB is that the input features (e.g.,  $\mathbf{F}_D$  and  $\mathbf{F}_{pan}^0$ ) have already been optimized by DSAM and SPAE for spectral calibration and spatial enhancement. Adding preconvolution layers here would make these refined features oversmoothed, especially the high-frequency edges in PAN. By directly feeding raw features into CAFBL, the crossmodal attention can better capture the intrinsic spatial—spectral relationships without interference from redundant filtering.

Following the above process, the feature  $\mathbf{F}_{R}^{0}$  after SSRM-1 and the shallow feature  $\mathbf{F}_{hs}^{0}$  are, then, fed into SSRM-2 together, resulting in the fused feature  $\mathbf{F}_{R}^{1}$  before the final fusion.

## Algorithm 2 DSAM

**Require:**  $\mathbf{F}_{M}$ ,  $\mathbf{F}_{ms}^{0}$ , compression ratio r = 161:  $\mathbf{F}_{d}^{1} = \text{Conv}_{3 \times 3}(\text{Conv}_{\text{res}}(\text{Cat}(\mathbf{F}_{M}, \mathbf{F}_{ms}^{0})))$ 2:  $\mathbf{F}_{d}^{2} = \text{Conv}_{1 \times 1}(\mathbf{F}_{ms}^{0})$ 3:  $\mathbf{U} = \text{GAP}(\mathbf{F}_{d}^{1} + \mathbf{F}_{d}^{2})$ 4:  $\mathbf{W}^{1} = \text{FC}_{1}(\text{FC}(\mathbf{U}))$ ,  $\mathbf{W}^{2} = \text{FC}_{2}(\text{FC}(\mathbf{U}))$ 5:  $\mathbf{W}_{s}^{1}$ ,  $\mathbf{W}_{s}^{2} = \text{softmax}(\mathbf{W}^{1}, \mathbf{W}^{2})$ 6: **return**  $\mathbf{W}_{s}^{1} \odot \mathbf{F}_{d}^{1} + \mathbf{W}_{s}^{2} \odot \mathbf{F}_{d}^{2}$ 

## D. Feature Reconstruction Module

After passing through SSRM-1 and SSRM-2, the final refined features are obtained and fed into the feature reconstruction module, as shown in Fig. 6, to generate the final HR HS image. The process is carried out in two stages. Initially, the features pass through a reconstruction convolutional layer. The original HS image is then upsampled and merged with

the derived features to improve the reconstruction of spectral information. This process is described as follows:

$$\mathbf{F}_{R} = \operatorname{Conv}_{3\times3} \left( CBRE \left( \mathbf{F}_{R}^{1} \right) \right) \tag{19}$$

$$\mathbf{Z} = \mathbf{F}_R + \mathrm{Up}(\mathbf{H}) \tag{20}$$

where the operation of  $CBRE(\cdot)$  is shown in (1), and  $Up(\mathbf{H})$  represents the upsampled HS image.

In this article, we use the  $L_1$  loss function to minimize the gap between the fused result and the reference image, as well as to optimize the network parameters.  $L_1$  loss can be expressed as

$$L_1 = \frac{1}{N} \sum_{n=1}^{N} \| \mathbf{Z}' - \mathbf{Z} \|_1$$
 (21)

where N represents the number of images in each batch,  $\mathbf{Z}'$  represents the reference image, and  $\mathbf{Z}$  represents the fused result.

## IV. EXPERIMENTS

## A. Datasets

Four remote sensing datasets, including two simulated and two real datasets, respectively, were used to thoroughly assess and validate the effectiveness of the suggested method. On the real datasets, the network was first trained on the reduced resolution data and then tested on the full resolution data.

1) Chikusei Dataset: The Headwall Hyperspec-VNIR-C image sensor was used to collect the Chikusei dataset in both urban and rural regions in Chikusei, Ibaraki, Japan. With a spatial resolution of 2.5 m and a spatial size of  $2517 \times 2335$ pixels, it has 128 spectral bands that span wavelengths from 363 to 1018 nm. The scene mainly consists of urban and rural areas. During the experiments, we first manually removed the obvious noisy bands, leaving 124 spectral bands. Additionally, we cropped the irregular black edges of the image, resulting in a final size of 2355  $\times$  2188. Then, Gaussian blurring was applied to the original image [50], and downsampling by a factor of 12 was performed to create the LR HS image. The MR MS image was obtained by downsampling by a factor of 4 after Gaussian blurring was applied in the spatial dimension. To create an eight-band MS image, the original spectral bands were uniformly split into eight groups in the spectral dimension. Finally, an HR PAN image was generated by averaging all spectral bands of the original image into a single band. Among them, the kernel size of the Gaussian blur filter we used for the blurred images is  $8 \times 8$ , and the standard deviation is 2 [45], [48].

Most regions of the entire image are cropped into cubic patches of size  $192 \times 192 \times 124$  to create training data pairs, where the dimensions of the PAN, MS, and HS images are  $192 \times 192$ ,  $48 \times 48 \times 8$ , and  $16 \times 16 \times 124$ , respectively. The remaining areas of the entire image are then cropped into patches of size  $384 \times 384 \times 124$  to serve as reference images for testing. In the test data, the sizes of the PAN, MS, and HS images are  $384 \times 384$ ,  $96 \times 96 \times 8$ , and  $32 \times 32 \times 124$ , respectively.

2) Pavia Center Dataset: The Reflective Optical System Imaging Spectrometer (ROSIS) was used to collect the Pavia Center Dataset in Pavia, northern Italy. With 102 spectral bands and a spectral range of 430–860 nm, the full image has

<!-- Page 9 -->

a spatial dimension of 1096 × 715 and a spatial resolution of 1.3 m. The main surface content includes buildings, roads, and trees. Similar to the Chikusei dataset, we manually removed certain noisy bands, retaining 98 bands. Using the same Gaussian blurring filter and downsampling factor as in the Chikusei dataset, we generated the LR HS, MR MS, and HR PAN images.

Most of the original image area is cropped into cubic patches of size 120 × 120 × 98, serving as reference images for the training data. The PAN, MS, and HS images used for training have sizes of 120 × 120, 30 × 30 × 8, and 10 × 10 × 98, respectively. The testing data are obtained from the bottom region of the original image, with the reference image for testing sized at 240 × 240 × 98 pixels. The PAN, MS, and HS images in the testing data have sizes of 240 × 240, 60 × 60 × 8, and 20 × 20 × 98, respectively.

*3) HZB Dataset:* The real dataset, HZB dataset, was collected by the ZiYuan-1 02D (ZY1E) satellite over an urban area south of Hangzhou Bay (HZB), providing PAN, MS, and HS images. The HS image has a spatial resolution of 30 m and a spatial size of 900 × 1400 pixels, with a spectral range covering 400–2500 nm. After removing uncalibrated and noisy bands, 137 out of the original 166 spectral bands remain for further use. The MS image has a spatial size of 2700 × 4200 with a spatial resolution of 10 m, covering eight spectral bands in the 452–1047-nm range. The PAN image has a spatial resolution of 2.5 m and a spatial size of 10800 × 16800, with a spectral range of 452–902 nm. Due to the lack of actual reference labels in real datasets, training samples and reference labels for the supervised network were generated according to Wald's protocol [51]. We uniformly perform blurring and downsampling operations on the original PAN, MS, and HS images. The downsampling ratio is the difference in spatial ratio between the PAN and HS images, which is 12 times. The original HS image serves as the reference image, and in this way, training image pairs are generated. The 70% of the original data were cropped into cubic patches for training, while the remaining region was used for testing. Specifically, the sizes of the PAN, MS, and HS images used for training were 192 × 192, 48 × 48 × 8, and 16 × 16 × 137, respectively. The trained model was, then, directly applied to the full-resolution data, where the original PAN, MS, and HS images were fused to test the full-resolution results. The sizes of the test images were 480 × 480, 120 × 120 × 8, and 40 × 40 × 137.

*4) YC Dataset:* The Yancheng (YC) dataset, centered around the eastern wetlands of YC, was also collected by the ZiYuan-1 02D satellite. For the same region, it provides PAN, MS, and HS images with sizes of 13200 × 11280, 3300 × 2820 × 8, and 1100 × 940 × 166, respectively. The spatial resolutions and spectral band ranges are consistent with those described for the HZB dataset. After removing uncalibrated and noisy bands, the HS image retains 111 bands.

The majority of the original image area was used to generate training data, while the remaining 30% was reserved for testing data. Specifically, the sizes of the PAN, MS, and HS images used for training were 192 × 192, 96 × 96 × 8, and 16 × 16 × 111, respectively. The PAN, MS, and HS images used for full resolution testing were 480 × 480, 120 × 120 × 8, and 40 × 40 × 111, respectively. The process for generating the training data and conducting the full-resolution experiments follows the same method as that used for the HZB dataset.

## *B. Experimental Setting*

In the experiments on the simulated datasets, we selected six metrics to quantitatively evaluate the fusion performance of all methods. These metrics include peak signal-to-noise ratio (PSNR), SSIM, spectral angle mapper (SAM), relative dimensionless global error in synthesis (ERGAS), root-meansquared error (RMSE), and correlation coefficient (CC).

Additionally, in the full-resolution experiments, to better demonstrate the advantages of the proposed method, we also employed the no-reference quality assessment metric QNR.

We evaluated the fusion performance of the proposed method with deep learning-based techniques like MGFEI [48], HMPNet [47], and HyperNet [45], as well as with other integrated PAN–MS–HS fusion methods that are currently in use, such as CNMF [37]. We also extended other deep learningbased methods—SMGU-Net [56], DCFNet [52], HyperPNN [18], and TFNet [53]—to support integrated PAN–MS–HS fusion. Additionally, we applied a sequential fusion strategy to the FUSE [16] and HySure [54] methods, where each method first fuses MS and HS images to obtain a preliminary HS image with enhanced spatial resolution. This result is, then, fused with the PAN image to achieve the final output. For DCFNet and TFNet, we added an HS image branch that mirrors the original structure. For HyperPNN, we incorporated an MS image branch. For SMGU-Net, we add a PAN image branch.

For all the above comparison methods, we use their default parameter settings. During training, we set the batch size to 4, the number of epochs to 500, and the learning rate to 0.0001, with parameter updates handled by the Adam optimizer [55]. All experiments are conducted on a computer equipped with a GeForce GTX 3090 GPU and an 11th Gen Intel Core i7 11700K processor. Deep learning methods are implemented using the PyTorch framework.

## *C. Experimental Results With Simulated Datasets*

*1) Experimental Results With the Chikusei Dataset:* Fig. 7 shows the comparison of the fusion results of different methods on the Chikusei dataset, using the 20th, 40th, and 60th bands to generate pseudo-color images. The first row shows full image comparisons, while the second row zooms in on regions marked in red boxes.

Classical HS fusion methods, despite combining PAN, MS, and HS information sequentially, accumulate spatial and spectral errors. For example, in Fig. 7(a) and (b), HySure and FUSE show unclear spatial contours with jagged edges and noticeable spectral distortion, evident in the overlapping colors in farmland and road areas. CMNF preserves spectral information better but suffers from greater spatial blurriness, particularly in the zoomed-in view images. Deep learning-based methods generally maintain both spatial and spectral information better than traditional methods although network architecture still influences performance. In Fig. 7(d), HyperPNN improves spatial detail compared to CMNF, but still falls short of the reference image. TFNet and DCFNet [Fig. 7(e) and (f)] show better spectral and spatial performances but still exhibit noticeable spatial distortions.

<!-- Page 10 -->

Fig. 7. Visual comparison of fusion results on Chikusei dataset. (a) HySure. (b) FUSE. (c) CMNF. (d) HyperPNN. (e) TFNet. (f) DCFNet. (g) HyperNet. (h) HMPNet. (i) SMGU-Net. (j) MGFEI. (k) Proposed. (l) Reference.

Fig. 8. Spectral error map of fusion results on Chikusei dataset. (a) HySure. (b) FUSE. (c) CMNF. (d) HyperPNN. (e) TFNet. (f) DCFNet. (g) HyperNet. (h) HMPNet. (i) SMGU-Net. (j) MGFEI. (k) Proposed. (l) Reference.

In Fig. 7(i), although SMGU-Net has improved in spatial quality, its detailed texture and spectral quality are still lacking. HyperNet, HMPNet, and MGFEI, designed for integrated PAN, MS, and HS fusion, demonstrate stronger performance [Fig. 7(g), (h), and (j)]. By improving spatial details while maintaining spectral accuracy, the proposed method [Fig. 7(k)] yields results that are most similar to the reference image. To further validate the proposed method's performance, Fig. 8 shows the spectral angle error map between the fused and reference images. The map shows that the proposed method produces the minimum error in both overall and edge details, indicating superior performance. The average quantitative metrics for all methods are presented in Table I. The proposed method receives the highest scores across all six assessment measures, confirming its competitive advantage.

*2) Experimental Results With the Pavia Dataset:* Fig. 9 shows visual fusion results on the Pavia dataset, using bands 10, 40, and 70 for pseudo-color images. The first row presents the overall fused images, while the second row zooms in on regions marked by yellow boxes.

For classical methods, HySure and FUSE retain more spatial information, while CNMF excels in spectral preservation.

<!-- Page 11 -->

TABLE I COMPARISON OF QUANTITATIVE EVALUATION METRICS ON CHIKUSEI DATASET. BOLD AND UNDERLINE: BEST AND SECOND BEST, RESPECTIVELY

| Method   | PSNR↑   | SSIM↑               | SAM↓   | ERGAS↓ | RMSE↓  | CC↑    |
|----------|---------|---------------------|--------|--------|--------|--------|
| HySure   | 35.5149 | 0.9654              | 4.0875 | 2.3251 | 0.0169 | 0.9541 |
| FUSE     | 33.7733 | 0.9578              | 5.0074 | 2.8437 | 0.0207 | 0.9403 |
| CMNF     | 34.0511 | 0.9596              | 4.8735 | 2.7673 | 0.0201 | 0.9451 |
| HyperPNN | 37.2688 | 0.9797              | 3.1248 | 1.9019 | 0.0138 | 0.9735 |
| TFNet    | 37.0092 | 0.9787              | 3.2289 | 1.9770 | 0.0142 | 0.9723 |
| DCFNet   | 38.5424 | 0.9820              | 2.9065 | 1.6583 | 0.0119 | 0.9773 |
| HyperNet | 38.8630 | 0.9847              | 2.7329 | 1.5976 | 0.0115 | 0.9793 |
| HMPNet   | 39.9680 | 0.9870              | 2.4966 | 1.4182 | 0.0101 | 0.9821 |
| SMGU-Net | 39.9044 | 0.9868              | 2.5125 | 1.4268 | 0.0102 | 0.9827 |
| MGFEI    | 40.0321 | 0.9876              | 2.4539 | 1.4018 | 0.0101 | 0.9845 |
| Proposed | 41.1152 | $\overline{0.9897}$ | 2.1845 | 1.2437 | 0.0089 | 0.9873 |

Fig. 9. Visual comparison of fusion results on Pavia Center dataset. (a) HySure. (b) FUSE. (c) CMNF. (d) HyperPNN. (e) TFNet. (f) DCFNet. (g) HyperNet. (h) HMPNet. (i) SMGU-Net. (j) MGFEI. (k) Proposed. (l) Reference.

However, all three methods exhibit noticeable spectral distortion [Fig. 9(a)–(b)]. Among deep learning-based methods, SMGU-Net, HyperPNN, TFNet, and DCFNet, despite incorporating extra branches, show suboptimal spectral fidelity and spatial detail compared to the proposed method. HyperNet, HMPNet, and MGFEI [Fig. 9 (g), (h), and (j)] offer similar visual performance but fall short in spectral preservation.

Fig. 10 further validates the proposed method with the spectral angle error map, where the proposed method achieves the smallest error, indicating its fusion results are closest to the reference image. Table II summarizes the quantitative evaluation metrics. While HySure, FUSE, and CNMF underperform compared to deep learning-based methods, their performance is similar to the simpler HyperPNN method. The proposed method outperforms all others across all metrics, demonstrating its superiority.

## *D. Experimental Results With Real Datasets*

*1) Experimental Results With the HZB Dataset:* Fig. 11 presents a visual comparison of full-resolution results on the HZB dataset using different methods. The pseudo-color images are generated using the 10th, 19th, and 29th bands. For comparison, Fig. 11(l)–(n) shows the original PAN, MS, and HS images with zoomed-in view regions.

In the zoomed-in view images [Fig. 11(a)–(c)], methods like HySure, FUSE, and CMNF exhibit spectral distortion and spatial blurring. FUSE shows severe space-spectral distortion, HySure has blocky artifacts, and CMNF shows smearing.

<!-- Page 12 -->

Fig. 10. Spectral error map of fusion results on Pavia Center dataset. (a) HySure. (b) FUSE. (c) CMNF. (d) HyperPNN. (e) TFNet. (f) DCFNet. (g) HyperNet. (h) HMPNet. (i) SMGU-Net. (j) MGFEI. (k) Proposed. (l) Reference.

TABLE II COMPARISON OF QUANTITATIVE EVALUATION METRICS ON PAVIA CENTER DATASET. BOLD AND UNDERLINE: BEST AND SECOND BEST, RESPECTIVELY

| Method   | PSNR↑   | SSIM↑               | SAM↓   | ERGAS↓              | RMSE↓               | CC↑    |  |
|----------|---------|---------------------|--------|---------------------|---------------------|--------|--|
| HySure   | 33.2503 | 0.9564              | 6.8208 | 3.5303              | 0.0217              | 0.9683 |  |
| FUSE     | 30.9674 | 0.9331              | 8.8844 | 4.5907              | 0.0283              | 0.9472 |  |
| CMNF     | 32.7927 | 0.9572              | 7.1908 | 3.7210              | 0.0229              | 0.9655 |  |
| HyperPNN | 35.9604 | 0.9770              | 4.9316 | 2.5831              | 0.0159              | 0.9838 |  |
| TFNet    | 35.4470 | 0.9736              | 5.2851 | 2.7397              | 0.0168              | 0.9812 |  |
| DCFNet   | 36.2067 | 0.9776              | 4.8181 | 2.5114              | 0.0154              | 0.9839 |  |
| HyperNet | 36.3784 | 0.9783              | 4.7495 | 2.4616              | 0.0151              | 0.9849 |  |
| HMPNet   | 37.1254 | 0.9807              | 4.3586 | 2.2586              | 0.0139              | 0.9868 |  |
| SMGU-Net | 36.7614 | 0.9801              | 4.5456 | 2.3552              | 0.0145              | 0.9860 |  |
| MGFEI    | 37.3395 | 0.9820              | 4.2307 | 2.2036              | 0.0135              | 0.9874 |  |
| Proposed | 38.0181 | $\overline{0.9842}$ | 3.9319 | $\overline{2.0382}$ | $\overline{0.0125}$ | 0.9894 |  |

TABLE III COMPARISON OF QUANTITATIVE EVALUATION METRICS ON FULL-RESOLUTION HZB DATASET. BOLD AND UNDERLINE: BEST AND SECOND BEST, RESPECTIVELY

| Method | HySure | FUSE   | CMNF   | HyperPNN | TFNet  | DCFNet | HyperNet | HMPNet | SMGU-Net | MGFEI  | Proposed |
|--------|--------|--------|--------|----------|--------|--------|----------|--------|----------|--------|----------|
| QNR↑   | 0.6143 | 0.3933 | 0.8134 | 0.7537   | 0.8126 | 0.8416 | 0.8126   | 0.8425 | 0.8368   | 0.8441 | 0.8452   |

Fig. 11(d)–(f) shows that HyperPNN lacks spatial clarity, with details like house features missing. TFNet exhibits blocky distortions, while DCFNet suffers from spectral mixing and a reddish distortion. The HyperNet method improves over the previous ones but still struggles with spatial preservation [Fig. 11(g)]. In Fig. 11(h)–(k), HMPNet and SMGU-Net exhibit varying degrees of spatial blurring and spectral distortion. MGFEI, while similar visually, shows blurred spatial details and inaccurate spectral transitions. The proposed method outperforms these approaches, as shown in the real dataset. Quantitatively, Table III confirms that the proposed method achieves the best QNR, highlighting its effectiveness.

To assess spectral performance, Fig. 12 shows the comparison of the spectral curves (i.e., reflectance/radiance intensity variations across contiguous narrow bands) of three typical land features, unused land, buildings, and roads between different fusion methods and the reference image. These pixellevel curves represent discrete samplings of the materials' spectral fingerprints, where fluctuations encode their unique spectral response characteristics. The proposed method (red curve) closely matches the reference HS image (black curve), demonstrating superior spectral fidelity in preserving these discriminative features.

*2) Experimental Results With the YC Dataset:* Fig. 13 presents full-resolution results and zoomed-in view images on the YC dataset. The pseudo-color images are generated using the 10th, 19th, and 29th bands.

In Fig. 13(a)–(c), like the HZB dataset, HySure shows severe blocky distortions, FUSE has significant spectral distortion with red artifacts, and CMNF suffers from missing spatial details, resulting in unclear features. In Fig. 13(d)–(f), Hyper-PNN exhibits the most severe distortions, especially abnormal red artifacts around buildings. TFNet is slightly clearer but still has noticeable noise, while DCFNet shows some improvement but remains spatially and spectrally deficient. In Fig. 13(g)–(k), HyperNet exhibits relatively high spatial blurring and spectral misalignment. HMPNet and SMGU-Net exhibit severe spectral and spatial distortions, respectively. While the MGFEI and proposed methods yield similar results, some deficiencies remain. For instance, in Fig. 13(h), building junction details

<!-- Page 13 -->

Fig. 11. Visual comparison of fusion results on full-resolution HZB dataset. (a) HySure. (b) FUSE. (c) CMNF. (d) HyperPNN. (e) TFNet. (f) DCFNet. (g) HyperNet. (h) HMPNet. (i) SMGU-Net. (j) MGFEI. (k) Proposed. (l) PAN. (m) MS. (n) HS.

Fig. 12. Comparison of single-pixel spectral values at three typical land features in the HZB dataset.

TABLE IV COMPARISON OF QUANTITATIVE EVALUATION METRICS ON FULL-RESOLUTION YC DATASET. BOLD AND UNDERLINE: BEST AND SECOND BEST, RESPECTIVELY

| Method | HySure | FUSE   | CMNF   | HyperPNN | TFNet  | DCFNet | HyperNet | HMPNet | SMGU-Net | MGFEI  | Proposed |
|--------|--------|--------|--------|----------|--------|--------|----------|--------|----------|--------|----------|
| QNR↑   | 0.7833 | 0.6407 | 0.7778 | 0.8038   | 0.7983 | 0.8148 | 0.8101   | 0.8144 | 0.8173   | 0.8200 | 0.8273   |

are unclear, and spectral distortions are visible. This highlights the superior performance of the proposed method, confirmed by the quantitative results in Table IV, which show that it achieves the best fusion in terms of spatial details and spectral fidelity.

Fig. 14 shows the comparison of the fusion results over typical land features farmland, buildings, and water. The proposed method (red curve) closely matches the reference HS image (black curve), demonstrating superior spectral fidelity.

<!-- Page 14 -->

Fig. 13. Visual comparison of fusion results on full-resolution YC dataset. (a) HySure. (b) FUSE. (c) CMNF. (d) HyperPNN. (e) TFNet. (f) DCFNet. (g) HyperNet. (h) HMPNet. (i) SMGU-Net. (j) MGFEI. (k) Proposed. (l) PAN. (m) MS. (n) HS.

Fig. 14. Comparison of single-pixel spectral values at three typical land features in the YC dataset.

## V. DISCUSSION

## *A. Contributions to Core Modules*

*1) Progressive Architecture:* Most existing integrated fusion methods, on a step-by-step approach, split fusion into MS–HS and PAN–HS stages, leading to cumulative distortion in intermediate results. In addition, the feature concatenationbased PAN–MS–HS fusion methods directly aggregate the trimodal features, causing cross-scale feature conflicts and redundancy. Our proposed PSSNet's progressive hierarchical fusion architecture (HS→ MS →PAN) achieves improvements in two aspects. First, through modality-specific processing pathways, it designs edge-optimized convolutional blocks for PAN to preserve geometrical details and spectral–spatial convolutions for HS to capture fine-grained spectral correlations, avoiding the "one-size-fits-all" feature extraction defect. Second, leveraging a residual-optimized modulation mechanism, it dynamically aligns spatial resolutions layer by layer, using residual connections to suppress the accumulation of spectral contamination and spatial blurring, addressing the spectral distortion in detail-injection architectures like HyperNet caused by the direct injection of PAN/MS information. This architecture upgrades the traditional "unified processing" linear flow to "progressive semantic enhancement," enabling layer-by-layer fusion and mutual optimization of spatial details and spectral information.

<!-- Page 15 -->

TABLE V QUANTITATIVE EVALUATION INDICATORS OF DIFFERENT MODULES ON THE CHIKUSEI DATASET

| Method         | PSNR↑   | SSIM↑  | SAM↓   | ERGAS↓ | RMSE↓  | CC↑    |
|----------------|---------|--------|--------|--------|--------|--------|
| w/o CAFB       | 36.8168 | 0.9726 | 3.3287 | 1.9904 | 0.0147 | 0.9762 |
| w/o SSRM       | 37.5143 | 0.9687 | 3.1066 | 1.8667 | 0.0133 | 0.9831 |
| w/o DSAM       | 38.6935 | 0.9864 | 2.6908 | 1.6630 | 0.0116 | 0.9842 |
| w/o CAFBL-SPAE | 38.3521 | 0.9883 | 2.4263 | 1.6898 | 0.0121 | 0.9865 |
| Proposed       | 41.1152 | 0.9897 | 2.1845 | 1.2437 | 0.0089 | 0.9873 |

TABLE VI COMPARISON OF PARAMETERS, FLOPS, AND TESTING TIME FOR DIFFERENT METHODS ON FULL-RESOLUTION HZB DATASET

| Method    | HySure | FUSE | CMNF  | HyperPNN | TFNet  | DCFNet | HyperNet | HMPNet | SMGU-Net | MGFEI   | Proposed |
|-----------|--------|------|-------|----------|--------|--------|----------|--------|----------|---------|----------|
| Params(M) | /      | /    | /     | 0.14     | 2.57   | 7.74   | 2.84     | 4.39   | 18.05    | 6.15    | 3.75     |
| Flops(G)  | /      | /    | /     | 32.60    | 141.97 | 191.37 | 653.61   | 1819   | 5819     | 1107.26 | 837.80   |
| Time(s)   | 293.87 | 7.67 | 27.68 | 2.68     | 2.37   | 2.28   | 3.16     | 2.63   | 3.10     | 2.45    | 2.91     |

- *2) Context-Aware Fusion Block:* The core innovation of CAFB lies in constructing a "cross-modal dynamic weighting" mechanism by designing a new spatial guiding spectral query–key interaction pattern, to dynamically adjust the contribution weights of different modalities. The existing integrated fusion methods, such as MGFEI's grouping feedback, fall short of modality-specific modulation, which can lead to spectral information being overshadowed by spatial textures. Compared to HyperNet's detail-injection architecture, the proposed CAFB's cross-modal attention captures long-range spatial–spectral dependencies, achieving deep interaction while avoiding redundant feature coupling, to fundamentally resolve the heterogeneous modality mismatch issue.
- *3) Spatial–Spectral Recombination Module:* The SSRM achieves innovation through a three-layer "decouplingreweighting-recombination" mechanism. First, the DSAM uses channel attention to suppress redundant spectral bands while enhancing discriminative spectral features through adaptive weights. Second, the SPEU extracts spatial priors via PANguided dual-pooling, hierarchically recombining with the purified spectral features output by DSAM. This design breaks the traditional "feature stacking" shallow interaction pattern. In addition, the SSRM avoids blind mixing of multimodal information through spectral–spatial feature decoupling, enabling spatial details (e.g., PAN edges) and spectral components (e.g., HS bands) to fuse in a "complementary rather than conflicting" manner, ultimately achieving nonredundant and efficient feature recombination.

## *B. Ablation Study*

Ablation tests on the Chikusei dataset were performed to validate the efficacy of each module in the proposed method, and the results are reported in Table V. The last row depicts the total efficiency of the proposed method as a benchmark.

The CAFB module is crucial for image fusion, enabling cross-modal feature interaction and capturing spatial–spectral dependencies between PAN, MS, and HS images. By dynamically adjusting feature weights, it enhances spatial details and preserves spectral integrity. Replacing the CAFB module with stacked convolutional layers processing concatenated features led to significant drops in all six evaluation metrics, with SAM and ERGAS dropping by 52% and 60%, respectively. This highlights the CAFB module's importance in cross-modal integration and quality improvement.

The SSRM module optimizes spatial–spectral fusion by calibrating spectral feature weights and enhancing spatial details. Ablations of the DSAM module and the CAFBL and SPEA components showed performance degradation, underscoring their importance. Replacing the SSRM module with standard convolutional operations caused substantial performance declines, demonstrating its superior spectral optimization and spatial enhancement capabilities.

## *C. E*ffi*ciency Comparison*

To compare computational efficiency, we measured the average computation time on the full-resolution HZB dataset. For deep learning-based methods, we also evaluated the number of parameters and floating-point operations (FLOPs). The results are shown in Table VI. It can be seen that the proposed network does not achieve optimal performance in terms of network parameters and FLOPs, but its average computation time is comparable to that of other deep learning networks. Further network structure optimization is required in the future, taking into account network complexity and computing efficiency, in order to minimize the computational burden and improve operational efficiency.

## VI. CONCLUSION

This article proposes a PSSNet for integrated fusion of PAN, MS, and HS images, optimizing feature utilization across modalities to achieve high-fidelity fusion. We developed a context-aware fusion module that integrates shifted window and cross-modal attention mechanisms to effectively capture spatial–spectral dependencies, thereby enhancing both spatial detail and spectral fidelity. Additionally, an SSRM dynamically adjusts spectral features, enriches multilevel spectral information, and interacts with spatial details to boost the spatial resolution in fused images. Experiments on two simulated datasets (Chikusei and Pavia) and two real datasets (HZB and YC) acquired by ZY-1 02D satellite with bundled PAN, MS, and HS images demonstrate that the proposed method effectively integrates PAN, MS, and HS data, delivering high spatial detail and preserving spectral information.

<!-- Page 16 -->

## REFERENCES

- [1] T. Petit, T. Bajjouk, P. Mouquet, S. Rochette, B. Vozel, and C. Delacourt, "Hyperspectral remote sensing of coral reefs by semi-analytical model inversion-comparison of different inversion setups," *Remote Sens. Environ.*, vol. 190, pp. 348–365, Mar. 2017.
- [2] Y. Huang et al., "Cross-scene wetland mapping on hyperspectral remote sensing images using adversarial domain adaptation network," *ISPRS J. Photogramm. Remote Sens.*, vol. 203, pp. 37–54, Sep. 2023.
- [3] Q. Liu, X. Meng, F. Shao, and S. Li, "Supervised-unsupervised combined deep convolutional neural networks for high-fidelity pansharpening," *Inf. Fusion*, vol. 89, pp. 292–304, Jan. 2023.
- [4] X. Meng, H. Shen, H. Li, L. Zhang, and R. Fu, "Review of the pansharpening methods for remote sensing images based on the idea of meta-analysis: Practical discussion and challenges," *Inf. Fusion*, vol. 46, pp. 102–113, Mar. 2019.
- [5] A. Mookambiga and V. Gomathi, "Comprehensive review on fusion techniques for spatial information enhancement in hyperspectral imagery," *Multidimensional Syst. Signal Process.*, vol. 27, no. 4, pp. 863–889, Oct. 2016.
- [6] M. Ciotola et al., "Hyperspectral pansharpening: Critical review, tools and future perspectives," 2024, *arXiv:2407.01355*.
- [7] L. Loncan et al., "Hyperspectral pansharpening: A review," *IEEE Geosci. Remote Sens. Mag.*, vol. 3, no. 3, pp. 27–46, Sep. 2015.
- [8] T.-M. Tu, S.-C. Su, H.-C. Shyu, and P. S. Huang, "A new look at IHSlike image fusion methods," *Inf. Fusion*, vol. 2, no. 3, pp. 177–186, Sep. 2001.
- [9] Y. Li, J. Qu, W. Dong, and Y. Zheng, "Hyperspectral pansharpening via improved PCA approach and optimal weighted fusion strategy," *Neurocomputing*, vol. 315, pp. 371–380, Nov. 2018.
- [10] M. D. Mura, G. Vivone, R. Restaino, P. Addesso, and J. Chanussot, "Global and local gram-Schmidt methods for hyperspectral pansharpening," in *Proc. Int. Geosci. Remote Sens. Symp. (IGARSS)*, Jul. 2015, pp. 37–40.
- [11] G. Vivone, R. Restaino, G. Licciardi, M. D. Mura, and J. Chanussot, "Multiresolution analysis and component substitution techniques for hyperspectral pansharpening," in *Proc. IEEE Geosci. Remote Sens. Symp.*, Jul. 2014, pp. 2649–2652.
- [12] X. Otazu, M. Gonzalez-Audicana, O. Fors, and J. Nunez, "Introduction of sensor spectral response into image fusion methods. application to wavelet-based methods," *IEEE Trans. Geosci. Remote Sens.*, vol. 43, no. 10, pp. 2376–2385, Oct. 2005.
- [13] G. Vivone, R. Restaino, and J. Chanussot, "Full scale regression-based injection coefficients for panchromatic sharpening," *IEEE Trans. Image Process.*, vol. 27, no. 7, pp. 3418–3431, Jul. 2018.
- [14] R. Restaino, G. Vivone, M. Dalla Mura, and J. Chanussot, "Fusion of multispectral and panchromatic images based on morphological operators," *IEEE Trans. Image Process.*, vol. 25, no. 6, pp. 2882–2895, Jun. 2016.
- [15] H. Lin and A. Zhang, "Fusion of hyperspectral and panchromatic images using improved HySure method," in *Proc. 2nd Int. Conf. Image, Vis. Comput. (ICIVC)*, Jun. 2017, pp. 489–493.
- [16] Q. Wei, N. Dobigeon, and J.-Y. Tourneret, "Fast fusion of multi-band images based on solving a Sylvester equation," *IEEE Trans. Image Process.*, vol. 24, no. 11, pp. 4109–4121, Nov. 2015.
- [17] F. Palsson, J. R. Sveinsson, and M. O. Ulfarsson, "A new pansharpening algorithm based on total variation," *IEEE Geosci. Remote Sens. Lett.*, vol. 11, no. 1, pp. 318–322, Jan. 2014.
- [18] L. He, J. Zhu, J. Li, A. Plaza, J. Chanussot, and B. Li, "HyperPNN: Hyperspectral pansharpening via spectrally predictive convolutional neural networks," *IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens.*, vol. 12, no. 8, pp. 3092–3100, Aug. 2019.
- [19] H. Wang, J. Zhang, and L. Huo, "Multiscale hyperspectral pansharpening network based on dual pyramid and transformer," *IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens.*, vol. 17, pp. 19786–19797, 2024.
- [20] G. Guarino, M. Ciotola, G. Vivone, and G. Scarpa, "Band-wise hyperspectral image pansharpening using CNN model propagation," *IEEE Trans. Geosci. Remote Sens.*, vol. 62, 2024, Art. no. 5500518.
- [21] L. He, D. Xi, J. Li, H. Lai, A. Plaza, and J. Chanussot, "Dynamic hyperspectral pansharpening CNNs," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, 2023, Art. no. 5504819.
- [22] R. Dian, S. Li, B. Sun, and A. Guo, "Recent advances and new guidelines on hyperspectral and multispectral image fusion," *Inf. Fusion*, vol. 69, pp. 40–51, May 2021.
- [23] N. Yokoya, C. Grohnfeldt, and J. Chanussot, "Hyperspectral and multispectral data fusion: A comparative review of the recent literature," *IEEE Geosci. Remote Sens. Mag.*, vol. 5, no. 2, pp. 29–56, Jun. 2017.

- [24] M. Selva, B. Aiazzi, F. Butera, L. Chiarantini, and S. Baronti, "Hypersharpening: A first approach on SIM-GA data," *IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens.*, vol. 8, no. 6, pp. 3008–3024, Jun. 2015.
- [25] R. Kawakami, Y. Matsushita, J. Wright, M. Ben-Ezra, Y.-W. Tai, and K. Ikeuchi, "High-resolution hyperspectral imaging via matrix factorization," in *Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2011, pp. 2329–2336.
- [26] N. Akhtar, F. Shafait, and A. Mian, "Bayesian sparse representation for hyperspectral image super resolution," in *Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2015, pp. 3631–3640.
- [27] N. Yokoya, T. Yairi, and A. Iwasaki, "Coupled nonnegative matrix factorization unmixing for hyperspectral and multispectral data fusion," *IEEE Trans. Geosci. Remote Sens.*, vol. 50, no. 2, pp. 528–537, Feb. 2012.
- [28] C. Lanaras, E. Baltsavias, and K. Schindler, "Hyperspectral superresolution by coupled spectral unmixing," in *Proc. IEEE Int. Conf. Comput. Vis. (ICCV)*, Dec. 2015, pp. 3586–3594.
- [29] S. Li, R. Dian, L. Fang, and J. M. Bioucas-Dias, "Fusing hyperspectral and multispectral images via coupled sparse tensor factorization," *IEEE Trans. Image Process.*, vol. 27, no. 8, pp. 4118–4130, Aug. 2018.
- [30] R. Dian, S. Li, L. Fang, T. Lu, and J. M. Bioucas-Dias, "Nonlocal sparse tensor factorization for semiblind hyperspectral and multispectral image fusion," *IEEE Trans. Cybern.*, vol. 50, no. 10, pp. 4469–4480, Oct. 2020.
- [31] Y. Xu, Z. Wu, J. Chanussot, P. Comon, and Z. Wei, "Nonlocal coupled tensor CP decomposition for hyperspectral and multispectral image fusion," *IEEE Trans. Geosci. Remote Sens.*, vol. 58, no. 1, pp. 348–362, Jan. 2020.
- [32] W. He, Y. Chen, N. Yokoya, C. Li, and Q. Zhao, "Hyperspectral superresolution via coupled tensor ring factorization," *Pattern Recognit.*, vol. 122, Feb. 2022, Art. no. 108280.
- [33] W. Sun et al., "Domain transform model driven by deep learning for anti-noise hyperspectral and multispectral image fusion," *IEEE Trans. Geosci. Remote Sens.*, vol. 62, 2023, Art. no. 5500117.
- [34] X. Wang, C. Cheng, S. Liu, R. Song, X. Wang, and L. Feng, "SS-INR: Spatial–spectral implicit neural representation network for hyperspectral and multispectral image fusion," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, 2023, Art. no. 5525214.
- [35] X. Cao, Y. Lian, K. Wang, C. Ma, and X. Xu, "Unsupervised hybrid network of transformer and CNN for blind hyperspectral and multispectral image fusion," *IEEE Trans. Geosci. Remote Sens.*, vol. 62, 2024, Art. no. 5507615.
- [36] S. Liu, S. Miao, S. Liu, B. Li, W. Hu, and Y.-D. Zhang, "Circle-Net: An unsupervised lightweight-attention cyclic network for hyperspectral and multispectral image fusion," *IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens.*, vol. 16, pp. 4499–4515, 2023.
- [37] N. Yokoya, T. Yairi, and A. Iwasaki, "Hyperspectral, multispectral, and panchromatic data fusion based on coupled non-negative matrix factorization," in *Proc. 3rd Workshop Hyperspectral Image Signal Process., Evol. Remote Sens. (WHISPERS)*, Jun. 2011, pp. 1–4.
- [38] X. Meng, H. Shen, H. Li, Q. Yuan, H. Zhang, and L. Zhang, "Improving the spatial resolution of hyperspectral image using panchromatic and multispectral images: An integrated method," in *Proc. 7th Workshop Hyperspectral Image Signal Process., Evol. Remote Sens. (WHISPERS)*, Jun. 2015, pp. 1–4.
- [39] M. A. Bendoumi and T. Benlefki, "Fusion of hyperspectral, multispectral, and panchromatic data based on spectral unmixing," in *Proc. Int. Conf. Signal, Image, Vis. Their Appl. (SIVA)*, Nov. 2018, pp. 1–5.
- [40] R. Arablouei, "Fusing multiple multiband images," *J. Imag.*, vol. 4, no. 10, p. 118, Oct. 2018.
- [41] X. Tian, W. Zhang, Y. Chen, Z. Wang, and J. Ma, "HyperFusion: A computational approach for hyperspectral, multispectral, and panchromatic image fusion," *IEEE Trans. Geosci. Remote Sens.*, vol. 60, 2022, Art. no. 5518216.
- [42] Q. Liu, X. Meng, S. Zhang, X. Li, and F. Shao, "A temporally insensitive spatio-temporal fusion method for remote sensing imagery via semantic prior regularization," *Inf. Fusion*, vol. 117, May 2025, Art. no. 102818.
- [43] W. Sun et al., "Generating high-resolution hyperspectral time series datasets based on unsupervised spatial–temporal-spectral fusion network incorporating a deep prior," *Inf. Fusion*, vol. 111, Nov. 2024, Art. no. 102499.
- [44] M. Hu, C. Wu, and L. Zhang, "GlobalMind: Global multi-head interactive self-attention network for hyperspectral change detection," *ISPRS J. Photogramm. Remote Sens.*, vol. 211, pp. 465–483, May 2024.

<!-- Page 17 -->

- [45] K. Li, W. Zhang, D. Yu, and X. Tian, "HyperNet: A deep network for hyperspectral, multispectral, and panchromatic image fusion," *ISPRS J. Photogramm. Remote Sens.*, vol. 188, pp. 30–44, Jun. 2022.
- [46] X. Meng et al., "Integrated fusion for panchromatic, multispectral, hyperspectral remote sensing images with different swath widths," *IEEE Geosci. Remote Sens. Lett.*, vol. 19, pp. 1–5, 2022.
- [47] X. Tian, K. Li, W. Zhang, Z. Wang, and J. Ma, "Interpretable modeldriven deep network for hyperspectral, multispectral, and panchromatic image fusion," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 35, no. 10, pp. 14382–14395, Oct. 2023.
- [48] X. Meng, X. Meng, Q. Liu, and S. Li, "MGFEI-Net: Multiscale grouping feedback embedded integrated network for panchromatic, multispectral, and hyperspectral image fusion," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, 2023, Art. no. 5529216.
- [49] X. Li, W. Wang, X. Hu, and J. Yang, "Selective kernel networks," in *Proc. IEEE*/*CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2019, pp. 510–519.
- [50] K. Ren, W. Sun, X. Meng, G. Yang, J. Peng, and J. Huang, "A locally optimized model for hyperspectral and multispectral images fusion," *IEEE Trans. Geosci. Remote Sens.*, vol. 60, 2022, Art. no. 5519015.
- [51] L. Wald, T. Ranchin, and M. Mangolini, "Fusion of satellite images of different spatial resolutions: Assessing the quality of resulting images," *Photogramm. Eng. Remote Sens.*, pp. 691–699, 1997.
- [52] X. Wu, T.-Z. Huang, L.-J. Deng, and T.-J. Zhang, "Dynamic cross feature fusion for remote sensing pansharpening," in *Proc. IEEE*/*CVF Int. Conf. Comput. Vis. (ICCV)*, Oct. 2021, pp. 14667–14676.
- [53] X. Liu, Q. Liu, and Y. Wang, "Remote sensing image fusion based on two-stream fusion network," *Inf. Fusion*, vol. 55, pp. 1–15, Mar. 2020.
- [54] M. Simoes, J. Bioucas-Dias, L. B. Almeida, and J. Chanussot, "A convex ˜ formulation for hyperspectral image superresolution via subspace-based regularization," *IEEE Trans. Geosci. Remote Sens.*, vol. 53, no. 6, pp. 3373–3388, Jun. 2015.
- [55] D. P. Kingma and J. Ba, "Adam: A method for stochastic optimization," 2014, *arXiv:1412.6980*.
- [56] J. Yan et al., "Spatial–spectral unfolding network with mutual guidance for multispectral and hyperspectral image fusion," *Pattern Recognit.*, vol. 161, May 2025, Art. no. 111277.

Yufu Bai received the B.S. degree from the School of Electronic and Information Engineering, Suzhou University of Science and Technology, Suzhou, China, in 2023. He is currently pursuing the M.S. degree with Ningbo University, Ningbo, China.

His research interests include deep learning for multisource image fusion in remote sensing and hyperspectral image processing.

Minchao Luo received the B.S. degree in electronic information engineering from Hunan University of Technology, Zhuzhou, China, in 2023. He is currently pursuing the M.S. degree with Ningbo University, Ningbo, China.

His research interests include visible and infrared image fusion, as well as object detection in remote sensing images.

Shenfu Zhang received the B.S. degree from Shaoxing University, Shaoxing, China, in 2022. He is currently pursuing the Ph.D. degree with Ningbo University, Ningbo, China.

His research interests include hyperspectral image processing and multisource data fusion classification.

source image fusion.

Qiang Liu received the B.S. degree from Shenyang Ligong University, Shenyang, China, in 2016, and the M.S. and Ph.D. degrees from the Faculty of Electrical Engineering and Computer Science, Ningbo University, Ningbo, China, in 2019 and 2024, respectively.

He is currently an Associate Professor with the School of Computer and Artificial Intelligence, Huanghuai University, Zhumadian, Henan, China. His research interests include deep learning for image processing, artificial intelligence, and multi-

Liang Chen received the B.S. and Ph.D. degrees from the University of Science and Technology of China, Hefei, China, in 2016 and 2023, respectively.

He is currently a Lecturer with the Faculty of Electrical Engineering and Computer Science, Ningbo University, Ningbo, China. His interests include hyperspectral image processing and target detection.

Weiwei Sun (Senior Member, IEEE) received the B.S. degree in surveying and mapping and the Ph.D. degree in cartography and geographic information engineering from Tongji University, Shanghai, China, in 2007 and 2013, respectively.

From 2011 to 2012, he studied with the Department of Applied Mathematics, University of Maryland College Park, College Park, MD, USA, working as a Visiting Scholar with the famous professor John Benedetto to study on the dimensionality reduction of hyperspectral image. From 2014 to 2016,

he studied with the State Key Laboratory for Information Engineering in Surveying, Mapping and Remote Sensing (LIESMARS), Wuhan University, Wuhan, China, working as a Post-Doctoral Researcher to study intelligent processing in hyperspectral imagery. From 2017 to 2018, he worked with the Department of Electrical and Computer Engineering, Mississippi State University, Starkville, MS, USA, and also worked as a Visiting Scholar of hyperspectral image processing. He is currently a Full Professor with Ningbo University, Ningbo, Zhejiang, China. He has published more than 80 journal articles. His research interests include hyperspectral image processing with machine learning.

Xiangchao Meng (Senior Member, IEEE) received the B.S. degree in geographic information system from Shandong University of Science and Technology, Qingdao, China, in 2012, and the Ph.D. degree in cartography and geography information system from Wuhan University, Wuhan, China, in 2017.

He studied with the College of Electrical and Information Engineering, Hunan University, Changsha, Hunan, China, working as a Post-Doctoral Researcher. He is currently a Professor with the

Faculty of Electrical Engineering and Computer Science, Ningbo University, Ningbo, China. His research interests include multisource data fusion and machine learning.