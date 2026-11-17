# Ask audit 2026-11-16 (dev, model=gpt-6-luna, reasoning effort=none)

Fill each case: relevant = yes/no/partial, citation_supported = yes/no/partial.

Rubric:
- relevant: yes = answers the question; partial = on topic but incomplete; no = off topic or wrong.
- citation_supported: yes = every claim is in a cited excerpt; partial = some claims are not; no = excerpts do not support the answer.

## q06 (ask) 7125 ms, 1300+79 tokens, top_distance=0.32863926887512207

**Q:** What does Vault's transit engine do?  
**Filters:** None  
**Expected items:** ['1f44fa699fbdaa46']  
**Cites a gold item (machine):** True

**Answer:** Vault’s transit secrets engine performs cryptographic operations on data in transit, primarily encrypting and decrypting it. It can also sign and verify data, generate hashes and HMACs, and provide random bytes. Vault does not store the data sent to it, so it can provide encryption as a service.[1]

- [1] `1f44fa699fbdaa46` https://learn.hashicorp.com/tutorials/vault/eaas-transit  
  > The transit secrets engine primary use case is to encrypt data. This relieves the burden of data encryption and decryption from the application developers and moves the burden to Vault. The transit secrets engine also provides the following features: Sign and verify data Generate hashes and HMACs of data Act as a source of random bytes Vault's transit secrets engine handles cryptographic functions on data-in-transit . Vault doesn't store the data sent to the secrets engine, so it can also be viewed as encryption as a service . Challenge Example Inc. recently made headlines for a massive data breach which exposed millions of their users' payment card accounts online. When they tracked down the problem they found that a new HVAC system with management software had been put into their data centers. This new system introduced vulnerabilities in their networks and exposed ports and IP addresses to the databases publicly. Solutions

- relevant: yes
- citation_supported: yes
- notes: 

## q07 (ask) 7988 ms, 1219+147 tokens, top_distance=0.29624390602111816

**Q:** How OpenCV is being used to recognize face in Java programming.  
**Filters:** None  
**Expected items:** ['bd7e7d9395b2585e']  
**Cites a gold item (machine):** True

**Answer:** OpenCV’s Java bindings are used to access its face-recognition module, which must be built manually because it is not included in the standard release. The module provides Eigenfaces, Fisherfaces, and Local Binary Patterns Histograms algorithms [1][3]. In the described Eigenfaces example, the program loads OpenCV, reads a CSV file containing images and labels, holds them in separate lists, removes one image for testing, trains the model on the remaining 399 images, and asks it to predict the held-out image’s label. A lower confidence value indicates a better prediction [4].

- [1] `bd7e7d9395b2585e` https://www.freecodecamp.org/news/facial-recognition-using-opencv-in-java-92fa40c22f62/  
  > By Manish Bansal Ever since the Artificial Intelligence boom began — or the iPhone X advertisement featuring the face unlock feature hit TV screens — I’ve wanted to try this technology. However, once I started googling about it, I typically only found code examples in Python. And being a Java enthusiast for seven years, I got demotivated seeing that. Therefore, I finally decided to hunt for Java open source libraries for this. Currently, there are various Java libraries out there. But the most popular one I found was OpenCV . OpenCV is an open source computer vision library that has tons of modules like object detection, face recognition, and augmented reality. Although this library is written in C++, it also offers battle-tested Java bindings. However, there is one issue. As part of its software release, it offers only a few modules (with Java bindings) out of the box — and facial recognition is not one of them. Therefore, to use it, you need to manually build it. Wait! What? Why?
- [3] `bd7e7d9395b2585e` https://www.freecodecamp.org/news/facial-recognition-using-opencv-in-java-92fa40c22f62/  
  > first . The only issues you will encounter at this point will be related to system environment variables or user library setup. FaceDetection : you can use this to test the face detection module. It is a different module from face recognition. This is a module which gets shipped along with standard release of OpenCV. As of this writing, we can provide an image as an input to the program, and it will detect all the faces inside the image. The output image has green rectangles drawn on all the detected faces. Input image for Face Detection program Output image of face detection program FaceRecognition: the OpenCV facerec module includes three algorithms: Eigenfaces Fisherfaces Local Binary Patterns Histograms. For technical details on all these algorithms, you can refer this official article. For demonstration purposes, I will show you how to use the Eigenfaces algorithm. First, you need to download
- [4] `bd7e7d9395b2585e` https://www.freecodecamp.org/news/facial-recognition-using-opencv-in-java-92fa40c22f62/  
  > After this, you can run the face recognition program. Below are the steps performed in the program: OpenCV library is loaded as usual. The .csv file is read, and two ArrayList(s) are created . One for the matrix of images and other for their corresponding labels. Out of the 400 input images, the last entry in the list data structure is removed and saved for testing the trained model later. After that, the remaining 399 images are used for training the Eigenfaces algorithm. Once training is complete, the model is asked to predict the label of the image we removed in step 3. Output of Face Recognition Program Here, we can observe that the algorithm is able to predict the label of our test subject with a confidence value of 1807. The lower the value, the better the prediction. Similarly, you can perform this exercise with two other algorithms. The C++ code can be downloaded from here and here . Update (27th Dec 2018)

- relevant: yes
- citation_supported: yes
- notes: 

## q08 (ask) 1928 ms, 1248+52 tokens, top_distance=0.3262196183204651

**Q:** What's the time complexity of inserting a node into a B+ tree?  
**Filters:** None  
**Expected items:** ['ec5068129a845350']  
**Cites a gold item (machine):** True

**Answer:** The worst-case time complexity of inserting a node into a B+ tree is Θ(log n), where n is the number of records in the tree.[1][2]

- [1] `ec5068129a845350` https://iq.opengenus.org/b-tree-search-insert-delete-operations/  
  > In either case, we will need to repeat the removal algorithm on the parent node to remove the “split key” that previously separated these merged nodes — unless the parent is the root and we are removing the final key from the root, in which case the merged node becomes the new root (and the tree has become one level shorter than before). The figure depicts the searching of an element in a B-Tree. **The figure illustrates the insertion of an element in a B+ Tree. B+ tree grows at the root and not at the leaves.** The figure illustrates the deletion of an element from a b+ tree. Complexity Worst case search time complexity: Θ(logn) Average case search time complexity: Θ(logn) Best case search time complexity: Θ(logn) Worst case insertion time complexity: Θ(logn) Worst case deletion time complexity: Θ(logn) Average case Space complexity: Θ(n) Worst case Space complexity: Θ(n) Pseudocode Searching 1) Apply Binary search on records. 2) If record with the search key is found
- [2] `fa0d7f37d6a419ca` https://opendsa-server.cs.vt.edu/ODSA/Books/CS3/html/BTree.html  
  > siblings, and the total reduced to two nodes. Thus, the nodes are always at least two thirds full. [ 1 ] Finally, here is an example of building a B+ Tree of order five. You can compare this to the example above of building a tree of order four with the same records. Settings Saving... Server Error Resubmit Figure 12.6.7: An example of building a B+ tree of degree 5 Click here for a visualization that will let you construct and interact with a \(\mathrm{B}^+\) tree. This visualization was written by David Galles of the University of San Francisco as part of his Data Structure Visualizations package. 12. 6.1.2. B-Tree Analysis ¶ The asymptotic cost of search, insertion, and deletion of records from B-trees, \(\mathrm{B}^+\) trees, and \(\mathrm{B}^*\) trees is \(\Theta(\log n)\) where \(n\) is the total number of records in the tree. However, the base of the log is the (average) branching factor of the tree. Typical database applications use extremely high branching factors,

- relevant: yes
- citation_supported: yes
- notes: 

## q09 (ask) 1790 ms, 1667+55 tokens, top_distance=0.436797559261322

**Q:** Can we use a public known initial value as the key in AES-GSM encryption?  
**Filters:** None  
**Expected items:** ['62cef9f9439b4963']  
**Cites a gold item (machine):** True

**Answer:** No. The initial value (IV) may be publicly known, but the AES key must remain secret and confidential. Using a publicly known value as the key would not meet that requirement.[1]

- [1] `62cef9f9439b4963` https://mkyong.com/java/java-aes-encryption-and-decryption/  
  > int index = 0; while (index < hex.length()) { result.add(hex.substring(index, Math.min(index + blockSize, hex.length()))); index += blockSize; } return result.toString(); } } 2. AES encryption and decryption. The AES-GSM is the most widely used authenticated cipher. This example will encrypt and decrypt a string using 256-bit AES in Galois Counter Mode (GCM) . The AES-GCM inputs: AES Secret key (256 bits) IV – 96 bits (12 bytes) Length (in bits) of authentication tag – 128 bits (16 bytes) 2.1 In Java, we use AES/GCM/NoPadding to represent the AES-GCM algorithm. For the encrypted output, we prefix the 16 bytes IV to the encrypted text (ciphertext), because we need the same IV for decryption. Is this ok if IV is publicly known? It is ok for IV to be publicly known, the only secret is the key, keep it private and confidential. This example will use AES to encrypt a plain text Hello World AES-GCM and later decrypt it back to the original plain text. EncryptorAesGcm.java

- relevant: yes
- citation_supported: yes
- notes: 

## q10 (ask) 2519 ms, 1535+128 tokens, top_distance=0.5900046825408936

**Q:** I want to integrate Twillo into my system and receive recepient reaction, how to track it via webhook?  
**Filters:** None  
**Expected items:** ['87d874a621649a2d']  
**Cites a gold item (machine):** True

**Answer:** Configure the SendGrid Event Webhook to receive engagement events, which report how recipients interact with email. These include opens, clicks, spam reports, unsubscribes, group unsubscribes, and group resubscribes [2][4]. Enable Open Tracking to receive open events [5]; to track subscriptions and preference changes, enable Subscription Tracking [3]. Secure webhook data in production with Signed Event Webhook, OAuth 2.0, or both [1].

- [1] `87d874a621649a2d` https://sendgrid.com/docs/for-developers/tracking-events/event/  
  > Event Webhook Reference Positive Feedback Negative Feedback (warning) Secure Event Webhook data in production To secure the Event Webhook data, use the Signed Event Webhook, OAuth 2.0, or both. Twilio stores categories and unique arguments in a field that shouldn't include personally identifiable information (PII). Twilio might use these categories and arguments for counting or other operations as SendGrid runs its systems. You can't redact or remove these fields. Never place PII in this field. Twilio SendGrid doesn't treat this data as PII. Twilio employees could see these values. These values get stored long-term even if you leave the Twilio SendGrid platform. To learn more about Event Webhook security, see Getting Started with the Event Webhook Security Features . Events events page anchor Positive Feedback Negative Feedback
- [2] `87d874a621649a2d` https://sendgrid.com/docs/for-developers/tracking-events/event/  
  > 11 "status" : "5.0.0" 12 } 13 ] Processed events processed-events page anchor Positive Feedback Negative Feedback Twilio SendGrid accepted and can deliver the message. Example processed event webhook response example-processed-event-webhook-response page anchor Copy code block 1 [ 2 { 3 "email" : "alex@example.com" , 4 "timestamp" : 1513299569 , 5 "pool" : { 6 "name" : "new_MY_test" , 7 "id" : 210 8 }, 9 "smtp-id" : "<14c5d75ce93.dfd.64b469@ismtpd-555>" , 10 "event" : "processed" , 11 "category" : "cat facts" , 12 "sg_event_id" : "rbtnWrG1DVDGGGFHFyun0A==" , 13 "sg_message_id" : "14c5d75ce93.dfd.64b469.filter0001.16648.5515E0B88.000000000000000000000" 14 } 15 ] Engagement events engagement-events page anchor Positive Feedback Negative Feedback Engagement events include open , click , spam report , unsubscribe , group unsubscribe , and group resubscribe . Expected properties for engagement events expected-properties-for-engagement-events page anchor Positive Feedback Negative Feedback
- [3] `87d874a621649a2d` https://sendgrid.com/docs/for-developers/tracking-events/event/  
  > Positive Feedback Negative Feedback Recipient clicked on the Opt Out of All Emails link. To track subscriptions, turn on Subscription Tracking . Example webhook response for unsubscribe events example-webhook-response-for-unsubscribe-events page anchor Copy code block 1 [ 2 { 3 "email" : "alex@example.com" , 4 "timestamp" : 1513299569 , 5 "event" : "unsubscribe" , 6 "category" : "cat facts" , 7 "sg_event_id" : "zz_BjPgU_5pS-J8vlfB1sg==" , 8 "sg_message_id" : "14c5d75ce93.dfd.64b469.filter0001.16648.5515E0B88.0" 9 } 10 ] Group resubscribe events group-resubscribe-events page anchor Positive Feedback Negative Feedback Recipient resubscribed to a specific group by updating their preferences. To track subscriptions, turn on Subscription Tracking . Example webhook response for group resubscribe events example-webhook-response-for-group-resubscribe-events page anchor Copy code block 1 [ 2 { 3 "email" : "alex@example.com" , 4 "timestamp" : 1513299569 , 5 "smtp-id" :
- [4] `87d874a621649a2d` https://sendgrid.com/docs/for-developers/tracking-events/event/  
  > Positive Feedback Negative Feedback When Twilio SendGrid and email service providers process email messages, these messages generate events that Twilio logs. Twilio tracks three types of events: delivery, engagement, and account. Delivery events that indicate the status of email delivery to the recipient. Engagement events that indicate how the recipient is interacting with the email. Account change events that indicate changes and impacts to your account. Delivery events delivery-events page anchor Positive Feedback Negative Feedback Delivery events cover messages that were bounced , delivered , deferred , dropped , or processed . Expected properties for delivery events expected-properties-for-delivery-events page anchor Positive Feedback Negative Feedback The following table identifies the properties each delivery type returns: Property Bounce Delivered Deferred Dropped Processed asm_group_id X X X X X bounce_classification X attempt X category X X X X X email X X X X X event X X X
- [5] `87d874a621649a2d` https://sendgrid.com/docs/for-developers/tracking-events/event/  
  > , 5 "ip" : "255.255.255.255" , 6 "useragent" : "Mozilla/5.0 (iPhone; CPU iPhone OS 7_1_2 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D257 Safari/9537.53" , 7 "event" : "click" , 8 "email" : "email@example.com" , 9 "timestamp" : 1249948800 , 10 "url" : "http://example.com/blog/news.html" , 11 "url_offset" : { 12 "index" : 0 , 13 "type" : "html" 14 }, 15 "unique_arg_key" : "unique_arg_value" , 16 "category" : [ "category1" , "category2" ], 17 "newsletter" : { 18 "newsletter_user_list_id" : "10557865" , 19 "newsletter_id" : "1943530" , 20 "newsletter_send_id" : "2308608" 21 }, 22 "asm_group_id" : 1 23 } 24 ] Open events open-events page anchor Positive Feedback Negative Feedback Recipient has opened the HTML message. To track opens, turn on Open Tracking . Example webhook response for open events example-webhook-response-for-open-events page anchor Copy code block 1 [ 2 { 3 "email" : "alex@example.com" , 4 "timestamp" : 1513299569 , 5 "event" : "open" , 6

- relevant: yes
- citation_supported: yes
- notes: multiple chunks from the same item

## q11 (filter) 2671 ms, 1234+62 tokens, top_distance=0.3851897716522217

**Q:** How to identify a problem that can be solved using Dynamic Programming?  
**Filters:** {'domain': 'www.geeksforgeeks.org'}  
**Expected items:** ['783c3656a3bbcbe2']  
**Cites a gold item (machine):** True

**Answer:** Look for a problem with a recursive solution that repeatedly solves the same subproblems. Dynamic Programming can store those results and reuse them instead of recomputing them; this often reduces an exponential-time solution to polynomial time.[1]

- [1] `783c3656a3bbcbe2` https://www.geeksforgeeks.org/dynamic-programming/  
  > Courses Sale Tutorials Interview Prep DSA Tutorial Interview Questions Quizzes Must Do Advanced DSA System Design Aptitude Puzzles Interview Corner DSA Python Dynamic Programming or DP Last Updated : 17 Oct, 2026 Dynamic Programming is an algorithmic technique with the following properties. It is mainly an optimization over plain recursion. Wherever we see a recursive solution that has repeated calls for the same inputs, we can optimize it using Dynamic Programming. The idea is to simply store the results of subproblems so that we do not have to re-compute them when needed later. This simple optimization typically reduces time complexities from exponential to polynomial. Some popular problems solved using Dynamic Programming are Fibonacci Numbers, Diff Utility ( Longest Common Subsequence ), Bellman–Ford Shortest Path , Floyd Warshall , Edit Distance and Matrix Chain Multiplication . Fundamentals Introduction Tabulation vs Memoization Basic Problems Fibonacci numbers Tribonacci Numbers

- relevant: yes
- citation_supported: yes
- notes: 

## q14 (filter) 1587 ms, 1192+48 tokens, top_distance=0.407556414604187

**Q:** That article I saved on Oct 12 about scaling systems, how do you get horizontal scalability?  
**Filters:** {'since': 20261012, 'until': 20261012}  
**Expected items:** ['4338a0684b4cd642']  
**Cites a gold item (machine):** True

**Answer:** Horizontal scalability is usually achieved through load balancing: spread requests across multiple resources, such as servers, so adding hardware increases capacity. [1][2]

- [1] `4338a0684b4cd642` https://lethain.com/introduction-to-architecting-systems-for-scale/  
  > If you had three and you add another, your capacity would increase by 33%. Let’s call this horizontal scalability . On the failure side, an ideal system isn’t disrupted by the loss of a server. Losing a server should simply decrease system capacity by the same amount it increased overall capacity when it was added. Let’s call this redundancy . Both horizontal scalability and redundancy are usually achieved via load balancing. (This article won’t address vertical scalability , as it is usually an undesirable property for a large system, as there is inevitably a point where it becomes cheaper to add capacity in the form of additional machines rather than additional resources of one machine, and redundancy and vertical scaling can be at odds with one-another.) Load balancing is the process of spreading requests across multiple resources according to some metric (random, round-robin, random with weighting for machine capacity, etc)
- [2] `4338a0684b4cd642` https://lethain.com/introduction-to-architecting-systems-for-scale/  
  > Few computer science or software development programs attempt to teach the building blocks of scalable systems. Instead, system architecture is usually picked up on the job by working through the pain of a growing product or by working with engineers who have already learned through that suffering process. In this post I’ll attempt to document some of the scalability architecture lessons I’ve learned while working on systems at Yahoo! and Digg . I’ve attempted to maintain a color convention for diagrams: green is an external request from an external client (an HTTP request from a browser, etc), blue is your code running in some container (a Django app running on mod_wsgi , a Python script listening to RabbitMQ , etc), and red is a piece of infrastructure (MySQL, Redis , RabbitMQ, etc). Load balancing The ideal system increases capacity linearly with adding hardware. In such a system, if you have one machine and add another, your capacity would double.

- relevant: yes
- citation_supported: yes
- notes: 

## q01 (vague) 1727 ms, 1183+31 tokens, top_distance=0.49313896894454956

**Q:** There's an article about a popular k-drama. What's the name of the k-drama?  
**Filters:** None  
**Expected items:** ['af4bdf3132b2fdee']  
**Cites a gold item (machine):** True

**Answer:** The K-drama is *Take Charge of My Heart*.[1]

- [1] `af4bdf3132b2fdee` https://time.com/article/2026/10/01/take-charge-of-my-heart-ending-explained  
  > Korean dramas are famously chaste compared to Western TV series. Though there are some exceptions , most K-dramas shy away from featuring even passionate kissing, let alone full-on sex scenes. But Take Charge of My Heart , Netflix’s latest Korean-language romance, adds a jolt, making  “skinship,” or the physical intimacy between two people, a central part of its premise. In the supernatural series, TV scriptwriter Na Bo-bae ( When the Phone Rings ’ Chae Soo-bin) has electrical currents coursing through her body, making it so she will zap anyone she touches with bare hands. Because of the condition, Bo-bae has never dated. The lack of real-world experience is hindering her latest TV drama script—a romance about a chaebol heiress and her bodyguard. Advertisement Meanwhile, chaebol heir Baek Ho-rang ( Trigger

- relevant: yes
- citation_supported: yes
- notes: 

## q29 (vague) 2071 ms, 1153+82 tokens, top_distance=0.5754047632217407

**Q:** What's the article about the king who has lots of wives?  
**Filters:** None  
**Expected items:** ['e8cd234919c4f656']  
**Cites a gold item (machine):** True

**Answer:** The article is about Henry VIII, whose 38-year reign included six marriages, his break with the Catholic Church, and major political and religious changes in England. It also explores places connected to his life, including Kent, Leeds Castle, Hever Castle, Oxford, and Cambridge.[1][2][5]

- [1] `e8cd234919c4f656` https://academytravel.com.au/blog/behind-the-throne-henry-viii-england-key-sites  
  > Behind the Throne History 18 Dec Written by Dr Lauren Mackay Getting to know Henry VIII Henry VIII is one of the most famous monarchs - in his 38-year reign he married six times, broke with the Catholic Church, and ruled during one of the most politically tumultuous periods in England’s history. When the 18-year-old Henry VIII ascended the throne of England in 1509, he was determined to epitomise the age as a Golden Renaissance Prince. His reign marked the shift from the medieval period to the early modern world, and the handsome, educated, and athletic Henry was devoted to new learning of the age, humanism, art, architecture, andstrengthening England’s national identity. By the end of his reign however, Henry had strayed far from the promise his reign once held, a paranoid, brutal tyrant of immeasurable cruelty, who executed two wives, friends and counsellors, and violently reshaped the religious and political landscape of his realm.
- [2] `e8cd234919c4f656` https://academytravel.com.au/blog/behind-the-throne-henry-viii-england-key-sites  
  > In this article, I will be taking you to key places connected to Henry’s life – where it feels, in parts, that only time, rather than space, separates us from this larger-than-life King. Henry the Lover - Kent Kent has strong links to the early decades of Henry’s life and reign, when he was loved and admired throughout his realm. Ambassadors described Henry as “most excellent in his personal endowments, but... likewise so gifted and adorned with mental accomplishments of every soil that we believe him to have few equals in the world” and “A most invincible King, whose acquirements and qualities are so many and excellent that I consider him to excel all who ever wore a crown”. Kent is also connected to Henry’s first two queens in particular - Katherine of Aragon (below) and Anne Boleyn. Anne’s tumultuous affair with Henry tends to eclipse the rest of his marriages, but it is Henry’s first marriage to Katherine which offers an insight into Henry as a young man.
- [5] `e8cd234919c4f656` https://academytravel.com.au/blog/behind-the-throne-henry-viii-england-key-sites  
  > Henry can be felt everywhere at Hever, from his famous personal padlock, which he took with him wherever he travelled, and which now adorns the main door in the dining hall, to the impressive collection of Tudor portraits, second only to that of the National Portrait Gallery in London. And we can get a glimpse into Anne and Henry’s tumultuous romance - two prayer books (below) which belonged to Anne Boleyn, bearing her inscriptions and signature, and messages which she exchanged with the King. For better or worse, this love affair changed the course of English history. Oxford & Cambridge The medieval towns of Oxford and Cambridge are the scholarly bookends of Henry’s life, and he left an indelible mark on both.

- relevant: yes
- citation_supported: yes
- notes: 

## q23 (find) 4038 ms, 1274+221 tokens, top_distance=0.3442257046699524

**Q:** What's the difference of UDP and TCP, and their usage?  
**Filters:** None  
**Expected items:** ['5c35d650e1d44697', 'ef75458f6e296e61', '6a4e30c82368e2a2']  
**Cites a gold item (machine):** True

**Answer:** UDP is connectionless and sends independent datagrams. It does not guarantee delivery, ordering, or that a datagram arrives only once, and it does not automatically retransmit lost or corrupted data. TCP is connection-oriented and provides reliable, ordered delivery: it uses acknowledgements and retransmits data when needed. TCP is a byte stream, so it does not preserve message boundaries, unlike UDP datagrams, whose length is supplied to the receiving application. [1][2]

Use TCP when reliable, ordered delivery is important. UDP is useful when low-latency delivery or message boundaries matter, or when an application wants to handle loss itself; examples include DNS, NFS, SNMP, some Skype services, and streaming media. In time-sensitive games, TCP’s ordered retransmission can delay newer data behind a lost packet, so applications may use UDP and implement their own reliability as needed. [3][4][5]

- [1] `5c35d650e1d44697` https://www.cs.dartmouth.edu/~campbell/cs60/socketprogramming.html  
  > User Datagram Protocol (UDP) UDP is a simple transport-layer protocol. The application writes a message to a UDP socket, which is then encapsulated in a UDP datagram, which is further encapsulated in an IP datagram, which is sent to the destination. There is no guarantee that a UDP will reach the destination, that the order of the datagrams will be preserved across the network or that datagrams arrive only once. The problem of UDP is its lack of reliability: if a datagram reaches its final destination but the checksum detects an error, or if the datagram is dropped in the network, it is not automatically retransmitted. Each UDP datagram is characterized by a length. The length of a datagram is passed to the receiving application along with the data. No connection is established between the client and the server and, for this reason, we say that UDP provides a connection-less service . It is described in RFC 768. Transmission Control Protocol (TCP) TCP provides a
- [2] `5c35d650e1d44697` https://www.cs.dartmouth.edu/~campbell/cs60/socketprogramming.html  
  > TCP provides a connection oriented service , since it is based on connections between clients and servers. TCP provides reliability. When a TCP client send data to the server, it requires an acknowledgement in return. If an acknowledgement is not received, TCP automatically retransmit the data and waits for a longer period of time. We have mentioned that UDP datagrams are characterized by a length. TCP is instead a byte-stream protocol, without any boundaries at all. TCP is described in RFC 793, RFC 1323, RFC 2581 and RFC 3390. Socket addresses IPv4 socket address structure is named sockaddr_in and is defined by including the <netinet/in.h> header. The POSIX definition is the following: struct in_addr{ in_addr_t s_addr;        /*32 bit IPv4 network byte ordered address*/ }; struct sockaddr_in { uint8_t sin_len; /* length of structure (16)*/ sa_family_t sin_family; /* AF_INET*/ in_port_t sin_port; /* 16 bit TCP or UDP port number */ struct in_addr sin_addr; /* 32 bit IPv4 address*/
- [3] `ef75458f6e296e61` https://gafferongames.com/post/reliability_ordering_and_congestion_avoidance_over_udp/  
  > The problem with TCP is that it abstracts data delivery as a reliable ordered stream. Because of this, if a packet is lost, TCP has to stop and wait for that packet to be resent. This interrupts the steady stream of packets because more recent packets must wait in a queue until the resent packet arrives, so packets are received in the same order they were sent. What we need is a different type of reliability. Instead of having all data treated as a reliable ordered stream, we want to send packets at a steady rate and get notified when packets are received by the other computer. This allows time sensitive data to get through without waiting for resent packets, while letting us make our own decision about how to handle packet loss at the application level. It is not possible to implement a reliability system with these properties using TCP, so we have no choice but to roll our own reliability on top of UDP. Sequence Numbers
- [4] `ef75458f6e296e61` https://gafferongames.com/post/reliability_ordering_and_congestion_avoidance_over_udp/  
  > Reliability and Congestion Avoidance over UDP Oct 20, 2008 16 min read Game Networking Introduction Hi, I’m Glenn Fiedler and welcome to Networking for Game Programmers . In the previous article , we added our own concept of virtual connection on top of UDP. In this article we’re going to add reliability, ordering and congestion avoidance to our virtual UDP connection. The Problem with TCP Those of you familiar with TCP know that it already has its own concept of connection, reliability-ordering and congestion avoidance, so why are we rewriting our own mini version of TCP on top of UDP? The issue is that multiplayer action games rely on a steady stream of packets sent at rates of 10 to 30 packets per second, and for the most part, the data contained is these packets is so time sensitive that only the most recent data is useful. This includes data such as player inputs, the position, orientation and velocity of each player character, and the state of physics objects in the world.
- [5] `5c35d650e1d44697` https://www.cs.dartmouth.edu/~campbell/cs60/socketprogramming.html  
  > <unistd.h> int close(int sockfd); UDP Socket API There are some fundamental differences between TCP and UDP sockets. UDP is a connection-less, unreliable, datagram protocol (TCP is instead connection-oriented, reliable and stream based). There are some instances when it makes to use UDP instead of TCP. Some popular applications built around UDP are DNS, NFS, SNMP and for example, some Skype services and streaming media. Figure 4 shows the the interaction between a UDP client and server. First of all, the client does not establish a connection with the server. Instead, the client just sends a datagram to the server using the sendto function which requires the address of the destination as a parameter. Similarly, the server does not accept a connection from a client. Instead, the server just calls the recvfrom function, which waits until data arrives from some client. recvfrom returns the IP address of the client, along with the datagram, so the server can send a response to the client.

- relevant: yes
- citation_supported: yes
- notes: 
